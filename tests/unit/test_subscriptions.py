"""Unit tests for the subscriptions module."""

import pytest
from datetime import datetime

from fhir_r4_mcp.subscriptions import (
    SubscriptionConfig,
    SubscriptionManager,
)
from fhir_r4_mcp.subscriptions.handlers import (
    LoggingHandler,
    SubscriptionNotification,
    WebhookHandler,
)


class TestSubscriptionConfig:
    """Tests for SubscriptionConfig class."""

    def test_default_config(self):
        """Test default configuration."""
        config = SubscriptionConfig(
            criteria="Observation?patient=Patient/123",
            channel_type="rest-hook",
            endpoint="https://example.com/webhook",
        )

        assert config.criteria == "Observation?patient=Patient/123"
        assert config.channel_type == "rest-hook"
        assert config.payload_type == "application/fhir+json"

    def test_custom_config(self):
        """Test custom configuration."""
        config = SubscriptionConfig(
            criteria="Patient?_id=123",
            channel_type="websocket",
            endpoint="wss://example.com/ws",
            payload_type="application/fhir+ndjson",
            headers={"X-Custom": "value"},
            reason="Test subscription",
        )

        assert config.channel_type == "websocket"
        assert config.headers["X-Custom"] == "value"
        assert config.reason == "Test subscription"


class TestSubscriptionNotification:
    """Tests for SubscriptionNotification class."""

    def test_notification_creation(self):
        """Test notification creation."""
        notification = SubscriptionNotification(
            subscription_id="sub-123",
            event_type="event-notification",
            event_number=1,
            timestamp=datetime.utcnow(),
            focus={"resourceType": "Observation", "id": "obs-123"},
        )

        assert notification.subscription_id == "sub-123"
        assert notification.event_number == 1
        assert notification.focus["id"] == "obs-123"

    def test_from_bundle(self):
        """Test parsing notification from FHIR Bundle."""
        bundle = {
            "resourceType": "Bundle",
            "type": "subscription-notification",
            "entry": [
                {
                    "resource": {
                        "resourceType": "SubscriptionStatus",
                        "subscription": {"reference": "Subscription/sub-123"},
                        "type": "event-notification",
                        "notificationEvent": [
                            {
                                "eventNumber": 5,
                                "focus": {"reference": "Observation/obs-456"},
                            }
                        ],
                    }
                },
                {
                    "fullUrl": "Observation/obs-456",
                    "resource": {
                        "resourceType": "Observation",
                        "id": "obs-456",
                        "status": "final",
                    },
                },
            ],
        }

        notification = SubscriptionNotification.from_bundle(bundle)

        assert notification.subscription_id == "sub-123"
        assert notification.event_type == "event-notification"
        assert notification.event_number == 5
        assert notification.focus["id"] == "obs-456"

    def test_from_empty_bundle(self):
        """Test parsing notification from empty bundle."""
        bundle = {
            "resourceType": "Bundle",
            "entry": [],
        }

        notification = SubscriptionNotification.from_bundle(bundle)

        assert notification.subscription_id == ""
        assert notification.focus is None


class TestWebhookHandler:
    """Tests for WebhookHandler class."""

    @pytest.fixture
    def handler(self):
        """Create a test handler."""
        return WebhookHandler()

    def test_handler_creation(self, handler):
        """Test handler creation."""
        assert handler._callbacks == []

    def test_register_callback(self, handler):
        """Test registering a callback."""
        callback = lambda n: None  # noqa: E731

        handler.register_callback(callback)

        assert callback in handler._callbacks

    def test_unregister_callback(self, handler):
        """Test unregistering a callback."""
        callback = lambda n: None  # noqa: E731
        handler.register_callback(callback)

        handler.unregister_callback(callback)

        assert callback not in handler._callbacks

    @pytest.mark.asyncio
    async def test_handle_notification(self, handler):
        """Test handling a notification."""
        received = []

        def callback(notification):
            received.append(notification)

        handler.register_callback(callback)

        notification = SubscriptionNotification(
            subscription_id="sub-123",
            event_type="event-notification",
            event_number=1,
            timestamp=datetime.utcnow(),
        )

        await handler.handle_notification(notification)

        assert len(received) == 1
        assert received[0].subscription_id == "sub-123"

    @pytest.mark.asyncio
    async def test_handle_handshake(self, handler):
        """Test that handshake notifications are skipped."""
        received = []

        def callback(notification):
            received.append(notification)

        handler.register_callback(callback)

        notification = SubscriptionNotification(
            subscription_id="sub-123",
            event_type="handshake",
            event_number=0,
            timestamp=datetime.utcnow(),
        )

        await handler.handle_notification(notification)

        # Handshake should not trigger callbacks
        assert len(received) == 0

    @pytest.mark.asyncio
    async def test_handle_webhook_request(self, handler):
        """Test handling a webhook HTTP request."""
        body = {
            "resourceType": "Bundle",
            "entry": [
                {
                    "resource": {
                        "resourceType": "SubscriptionStatus",
                        "subscription": {"reference": "Subscription/sub-123"},
                        "type": "event-notification",
                        "notificationEvent": [{"eventNumber": 1}],
                    }
                }
            ],
        }

        response = await handler.handle_webhook_request(body)

        assert response["status"] == "ok"


class TestLoggingHandler:
    """Tests for LoggingHandler class."""

    @pytest.mark.asyncio
    async def test_logging_handler(self, caplog):
        """Test logging handler logs notifications."""
        handler = LoggingHandler(log_level="info")

        notification = SubscriptionNotification(
            subscription_id="sub-123",
            event_type="event-notification",
            event_number=1,
            timestamp=datetime.utcnow(),
            focus={"resourceType": "Patient", "id": "pat-456"},
        )

        await handler.handle_notification(notification)

        # Handler should have logged the notification
        # (caplog captures log output in tests)


class TestSubscriptionManager:
    """Tests for SubscriptionManager class."""

    @pytest.fixture
    def manager(self):
        """Create a test manager."""
        return SubscriptionManager()

    def test_manager_creation(self, manager):
        """Test manager creation."""
        assert len(manager._subscriptions) == 0

    def test_get_managed_subscriptions(self, manager):
        """Test getting managed subscriptions."""
        subscriptions = manager.get_managed_subscriptions()

        assert subscriptions == []

    def test_record_error(self, manager):
        """Test recording an error for a subscription."""
        from fhir_r4_mcp.subscriptions.manager import ManagedSubscription

        # Add a subscription manually
        sub = ManagedSubscription(
            id="sub-123",
            connection_id="conn-1",
            config=SubscriptionConfig(
                criteria="Patient?_id=123",
                channel_type="rest-hook",
                endpoint="https://example.com",
            ),
            status="active",
        )
        manager._subscriptions["sub-123"] = sub

        # Record error
        manager.record_error("sub-123", "Connection failed")

        assert sub.last_error == "Connection failed"
        assert sub.error_count == 1

        # Record another error
        manager.record_error("sub-123", "Timeout")

        assert sub.last_error == "Timeout"
        assert sub.error_count == 2

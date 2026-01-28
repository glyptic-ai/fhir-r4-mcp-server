"""FHIR Subscription notification handlers.

This module provides handlers for processing subscription notifications
from FHIR servers via various channels (REST hooks, WebSocket, etc.).
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable

import httpx

from fhir_r4_mcp.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class SubscriptionNotification:
    """A notification received from a FHIR subscription."""

    subscription_id: str
    event_type: str  # handshake | heartbeat | event-notification
    event_number: int
    timestamp: datetime
    focus: dict[str, Any] | None = None  # The resource that triggered the notification
    additional_context: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_bundle(cls, bundle: dict[str, Any]) -> "SubscriptionNotification":
        """Parse a notification from a FHIR Bundle.

        Args:
            bundle: Notification Bundle from FHIR server

        Returns:
            Parsed SubscriptionNotification
        """
        # Extract subscription status from first entry
        entries = bundle.get("entry", [])

        subscription_id = ""
        event_type = "event-notification"
        event_number = 0
        focus = None
        context: list[dict[str, Any]] = []

        for entry in entries:
            resource = entry.get("resource", {})
            resource_type = resource.get("resourceType")

            if resource_type == "SubscriptionStatus":
                subscription_id = resource.get("subscription", {}).get("reference", "")
                subscription_id = subscription_id.replace("Subscription/", "")
                event_type = resource.get("type", event_type)

                notification_events = resource.get("notificationEvent", [])
                if notification_events:
                    event_number = notification_events[0].get("eventNumber", 0)
                    focus_ref = notification_events[0].get("focus", {})
                    if focus_ref.get("reference"):
                        # Focus is a reference, need to find the resource in context
                        focus_ref_str = focus_ref["reference"]
                        for ctx_entry in entries:
                            ctx_resource = ctx_entry.get("resource", {})
                            full_url = ctx_entry.get("fullUrl", "")
                            if focus_ref_str in full_url:
                                focus = ctx_resource
                                break

            elif resource_type not in ("SubscriptionStatus",):
                context.append(resource)

        return cls(
            subscription_id=subscription_id,
            event_type=event_type,
            event_number=event_number,
            timestamp=datetime.utcnow(),
            focus=focus,
            additional_context=context,
        )


# Type for notification callback
NotificationCallback = Callable[[SubscriptionNotification], Any]


class SubscriptionHandler(ABC):
    """Abstract base class for subscription notification handlers."""

    @abstractmethod
    async def handle_notification(
        self,
        notification: SubscriptionNotification,
    ) -> None:
        """Handle a subscription notification.

        Args:
            notification: The notification to handle
        """
        pass

    @abstractmethod
    async def start(self) -> None:
        """Start the handler."""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Stop the handler."""
        pass


class WebhookHandler(SubscriptionHandler):
    """Handler for REST hook subscription notifications.

    This handler can receive webhook callbacks from FHIR servers
    and forward them to registered callbacks.
    """

    def __init__(
        self,
        callbacks: list[NotificationCallback] | None = None,
        retry_count: int = 3,
        retry_delay: float = 1.0,
    ) -> None:
        """Initialize the webhook handler.

        Args:
            callbacks: List of callback functions to invoke
            retry_count: Number of retries for failed callbacks
            retry_delay: Delay between retries in seconds
        """
        self._callbacks: list[NotificationCallback] = callbacks or []
        self._retry_count = retry_count
        self._retry_delay = retry_delay
        self._running = False

    def register_callback(self, callback: NotificationCallback) -> None:
        """Register a callback for notifications.

        Args:
            callback: Callback function to register
        """
        self._callbacks.append(callback)

    def unregister_callback(self, callback: NotificationCallback) -> None:
        """Unregister a callback.

        Args:
            callback: Callback function to unregister
        """
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    async def handle_notification(
        self,
        notification: SubscriptionNotification,
    ) -> None:
        """Handle an incoming webhook notification.

        Args:
            notification: The parsed notification
        """
        logger.info(
            f"Received notification for subscription {notification.subscription_id}, "
            f"event #{notification.event_number}, type: {notification.event_type}"
        )

        # Skip handshake events
        if notification.event_type == "handshake":
            logger.debug("Handshake notification received")
            return

        # Invoke all callbacks
        for callback in self._callbacks:
            try:
                result = callback(notification)
                if asyncio.iscoroutine(result):
                    await result

            except Exception as e:
                logger.error(f"Callback error: {e}")

    async def handle_webhook_request(
        self,
        body: dict[str, Any],
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Handle an incoming webhook HTTP request.

        This method should be called from your HTTP server
        when a webhook notification is received.

        Args:
            body: The request body (FHIR Bundle)
            headers: Request headers

        Returns:
            Response to send back
        """
        try:
            # Parse the notification bundle
            notification = SubscriptionNotification.from_bundle(body)

            # Handle it
            await self.handle_notification(notification)

            return {"status": "ok"}

        except Exception as e:
            logger.error(f"Failed to handle webhook: {e}")
            return {"status": "error", "message": str(e)}

    async def start(self) -> None:
        """Start the webhook handler."""
        self._running = True
        logger.info("Webhook handler started")

    async def stop(self) -> None:
        """Stop the webhook handler."""
        self._running = False
        logger.info("Webhook handler stopped")


class ForwardingHandler(SubscriptionHandler):
    """Handler that forwards notifications to another endpoint.

    Useful for relaying notifications to external services
    or transforming them before delivery.
    """

    def __init__(
        self,
        target_url: str,
        headers: dict[str, str] | None = None,
        timeout: float = 30.0,
        transform: Callable[[SubscriptionNotification], dict[str, Any]] | None = None,
    ) -> None:
        """Initialize the forwarding handler.

        Args:
            target_url: URL to forward notifications to
            headers: Custom headers to include
            timeout: Request timeout in seconds
            transform: Optional function to transform notifications
        """
        self._target_url = target_url
        self._headers = headers or {"Content-Type": "application/json"}
        self._timeout = timeout
        self._transform = transform

    async def handle_notification(
        self,
        notification: SubscriptionNotification,
    ) -> None:
        """Forward a notification to the target endpoint.

        Args:
            notification: The notification to forward
        """
        # Transform notification if transformer provided
        if self._transform:
            payload = self._transform(notification)
        else:
            payload = {
                "subscription_id": notification.subscription_id,
                "event_type": notification.event_type,
                "event_number": notification.event_number,
                "timestamp": notification.timestamp.isoformat(),
                "focus": notification.focus,
                "context": notification.additional_context,
            }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    self._target_url,
                    json=payload,
                    headers=self._headers,
                )

                if response.is_success:
                    logger.debug(f"Forwarded notification to {self._target_url}")
                else:
                    logger.warning(
                        f"Forward failed: {response.status_code} - {response.text}"
                    )

        except Exception as e:
            logger.error(f"Failed to forward notification: {e}")

    async def start(self) -> None:
        """Start the forwarding handler."""
        logger.info(f"Forwarding handler started, target: {self._target_url}")

    async def stop(self) -> None:
        """Stop the forwarding handler."""
        logger.info("Forwarding handler stopped")


class LoggingHandler(SubscriptionHandler):
    """Simple handler that logs notifications.

    Useful for debugging and development.
    """

    def __init__(self, log_level: str = "info") -> None:
        """Initialize the logging handler.

        Args:
            log_level: Log level to use (debug, info, warning)
        """
        self._log_level = log_level

    async def handle_notification(
        self,
        notification: SubscriptionNotification,
    ) -> None:
        """Log a notification.

        Args:
            notification: The notification to log
        """
        message = (
            f"Subscription notification: "
            f"id={notification.subscription_id}, "
            f"type={notification.event_type}, "
            f"event={notification.event_number}"
        )

        if notification.focus:
            resource_type = notification.focus.get("resourceType", "Unknown")
            resource_id = notification.focus.get("id", "")
            message += f", focus={resource_type}/{resource_id}"

        if self._log_level == "debug":
            logger.debug(message)
        elif self._log_level == "warning":
            logger.warning(message)
        else:
            logger.info(message)

    async def start(self) -> None:
        """Start the logging handler."""
        pass

    async def stop(self) -> None:
        """Stop the logging handler."""
        pass

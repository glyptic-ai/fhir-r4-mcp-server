"""FHIR R4 Subscription Manager.

This module manages FHIR Subscriptions for real-time notifications
when resources matching specified criteria are created or modified.

See: https://hl7.org/fhir/R4/subscription.html
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from fhir_r4_mcp.core.client import fhir_client
from fhir_r4_mcp.utils.errors import FHIRError, FHIRValidationError
from fhir_r4_mcp.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class SubscriptionConfig:
    """Configuration for a FHIR Subscription."""

    criteria: str  # Search criteria (e.g., "Observation?patient=Patient/123")
    channel_type: str  # rest-hook | websocket | email | message
    endpoint: str  # Destination URL for notifications
    payload_type: str = "application/fhir+json"  # Content type
    headers: dict[str, str] = field(default_factory=dict)  # Custom headers
    timeout_seconds: int = 60  # Request timeout
    reason: str | None = None  # Reason for the subscription


@dataclass
class ManagedSubscription:
    """A subscription managed by this server."""

    id: str
    connection_id: str
    config: SubscriptionConfig
    status: str  # requested | active | error | off
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_error: str | None = None
    error_count: int = 0


class SubscriptionManager:
    """Manager for FHIR Subscriptions.

    This class handles creation, tracking, and management of
    FHIR Subscriptions across multiple connections.
    """

    def __init__(self) -> None:
        """Initialize the subscription manager."""
        self._subscriptions: dict[str, ManagedSubscription] = {}

    def _generate_id(self, connection_id: str) -> str:
        """Generate a unique subscription ID."""
        import uuid

        return f"{connection_id}:{uuid.uuid4().hex[:8]}"

    async def create_subscription(
        self,
        connection_id: str,
        config: SubscriptionConfig,
    ) -> dict[str, Any]:
        """Create a new subscription on the FHIR server.

        Args:
            connection_id: FHIR connection to use
            config: Subscription configuration

        Returns:
            Created Subscription resource
        """
        # Validate channel type
        valid_channels = ["rest-hook", "websocket", "email", "message"]
        if config.channel_type not in valid_channels:
            raise FHIRValidationError(
                message=f"Invalid channel type: {config.channel_type}",
                field="channel_type",
                details={"valid_types": valid_channels},
            )

        # Build subscription resource
        subscription: dict[str, Any] = {
            "resourceType": "Subscription",
            "status": "requested",
            "criteria": config.criteria,
            "channel": {
                "type": config.channel_type,
                "endpoint": config.endpoint,
                "payload": config.payload_type,
            },
        }

        if config.reason:
            subscription["reason"] = config.reason

        if config.headers:
            subscription["channel"]["header"] = [
                f"{k}: {v}" for k, v in config.headers.items()
            ]

        try:
            # Create on FHIR server
            result = await fhir_client.post(connection_id, "Subscription", subscription)

            # Track locally
            sub_id = result.get("id", self._generate_id(connection_id))
            managed = ManagedSubscription(
                id=sub_id,
                connection_id=connection_id,
                config=config,
                status=result.get("status", "requested"),
            )
            self._subscriptions[sub_id] = managed

            logger.info(f"Created subscription {sub_id} for criteria: {config.criteria}")

            return result

        except FHIRError:
            raise
        except Exception as e:
            logger.error(f"Failed to create subscription: {e}")
            raise FHIRError(f"Failed to create subscription: {e}")

    async def list_subscriptions(
        self,
        connection_id: str,
        status: str | None = None,
    ) -> dict[str, Any]:
        """List subscriptions on a FHIR server.

        Args:
            connection_id: FHIR connection to query
            status: Optional status filter

        Returns:
            Bundle of Subscription resources
        """
        params: dict[str, Any] = {"_count": 100}
        if status:
            params["status"] = status

        try:
            result = await fhir_client.search(connection_id, "Subscription", params)
            return result

        except FHIRError:
            raise
        except Exception as e:
            logger.error(f"Failed to list subscriptions: {e}")
            raise FHIRError(f"Failed to list subscriptions: {e}")

    async def get_subscription(
        self,
        connection_id: str,
        subscription_id: str,
    ) -> dict[str, Any]:
        """Get a specific subscription.

        Args:
            connection_id: FHIR connection to query
            subscription_id: ID of the subscription

        Returns:
            Subscription resource
        """
        try:
            result = await fhir_client.read(connection_id, "Subscription", subscription_id)

            # Update local tracking if we have it
            if subscription_id in self._subscriptions:
                self._subscriptions[subscription_id].status = result.get("status", "unknown")

            return result

        except FHIRError:
            raise
        except Exception as e:
            logger.error(f"Failed to get subscription: {e}")
            raise FHIRError(f"Failed to get subscription: {e}")

    async def delete_subscription(
        self,
        connection_id: str,
        subscription_id: str,
    ) -> bool:
        """Delete a subscription.

        Args:
            connection_id: FHIR connection to use
            subscription_id: ID of the subscription to delete

        Returns:
            True if deleted successfully
        """
        try:
            await fhir_client.delete(connection_id, f"Subscription/{subscription_id}")

            # Remove from local tracking
            if subscription_id in self._subscriptions:
                del self._subscriptions[subscription_id]

            logger.info(f"Deleted subscription {subscription_id}")
            return True

        except FHIRError:
            raise
        except Exception as e:
            logger.error(f"Failed to delete subscription: {e}")
            raise FHIRError(f"Failed to delete subscription: {e}")

    async def update_status(
        self,
        connection_id: str,
        subscription_id: str,
        status: str,
    ) -> dict[str, Any]:
        """Update a subscription's status.

        Args:
            connection_id: FHIR connection to use
            subscription_id: ID of the subscription
            status: New status (requested | active | error | off)

        Returns:
            Updated Subscription resource
        """
        valid_statuses = ["requested", "active", "error", "off"]
        if status not in valid_statuses:
            raise FHIRValidationError(
                message=f"Invalid status: {status}",
                field="status",
                details={"valid_statuses": valid_statuses},
            )

        try:
            # Get current subscription
            current = await fhir_client.read(connection_id, "Subscription", subscription_id)

            # Update status
            current["status"] = status

            # Update on server
            result = await fhir_client.put(
                connection_id,
                f"Subscription/{subscription_id}",
                current,
            )

            # Update local tracking
            if subscription_id in self._subscriptions:
                self._subscriptions[subscription_id].status = status

            logger.info(f"Updated subscription {subscription_id} status to {status}")

            return result

        except FHIRError:
            raise
        except Exception as e:
            logger.error(f"Failed to update subscription status: {e}")
            raise FHIRError(f"Failed to update subscription status: {e}")

    def get_managed_subscriptions(
        self,
        connection_id: str | None = None,
    ) -> list[ManagedSubscription]:
        """Get locally managed subscriptions.

        Args:
            connection_id: Optional filter by connection

        Returns:
            List of managed subscriptions
        """
        subscriptions = list(self._subscriptions.values())

        if connection_id:
            subscriptions = [s for s in subscriptions if s.connection_id == connection_id]

        return subscriptions

    def record_error(
        self,
        subscription_id: str,
        error: str,
    ) -> None:
        """Record an error for a subscription.

        Args:
            subscription_id: ID of the subscription
            error: Error message
        """
        if subscription_id in self._subscriptions:
            sub = self._subscriptions[subscription_id]
            sub.last_error = error
            sub.error_count += 1
            logger.warning(f"Subscription {subscription_id} error ({sub.error_count}): {error}")


# Global subscription manager instance
subscription_manager = SubscriptionManager()

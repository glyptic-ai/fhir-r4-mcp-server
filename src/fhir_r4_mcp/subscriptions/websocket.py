"""WebSocket support for FHIR Subscriptions.

This module provides WebSocket-based real-time notifications
for FHIR Subscriptions.

Requires: pip install fhir-r4-mcp-server[websocket]
"""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable

from fhir_r4_mcp.subscriptions.handlers import (
    NotificationCallback,
    SubscriptionHandler,
    SubscriptionNotification,
)
from fhir_r4_mcp.utils.logging import get_logger

logger = get_logger(__name__)

try:
    import websockets
    from websockets.legacy.client import WebSocketClientProtocol

    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    websockets = None  # type: ignore
    WebSocketClientProtocol = None  # type: ignore


@dataclass
class WebSocketConnection:
    """A managed WebSocket connection."""

    subscription_id: str
    connection_id: str
    url: str
    websocket: Any | None = None  # WebSocketClientProtocol
    connected: bool = False
    reconnect_attempts: int = 0
    last_message_at: datetime | None = None
    error: str | None = None


class WebSocketManager:
    """Manager for WebSocket subscription connections.

    Handles connecting to FHIR servers via WebSocket for
    real-time subscription notifications.
    """

    def __init__(
        self,
        callbacks: list[NotificationCallback] | None = None,
        max_reconnect_attempts: int = 5,
        reconnect_delay: float = 5.0,
        ping_interval: float = 30.0,
    ) -> None:
        """Initialize the WebSocket manager.

        Args:
            callbacks: Callbacks for notifications
            max_reconnect_attempts: Max reconnection attempts
            reconnect_delay: Delay between reconnection attempts
            ping_interval: Interval for ping/pong keepalive

        Raises:
            ImportError: If websockets package is not installed
        """
        if not WEBSOCKETS_AVAILABLE:
            raise ImportError(
                "WebSocket support requires the 'websockets' package. "
                "Install with: pip install fhir-r4-mcp-server[websocket]"
            )

        self._callbacks: list[NotificationCallback] = callbacks or []
        self._max_reconnect = max_reconnect_attempts
        self._reconnect_delay = reconnect_delay
        self._ping_interval = ping_interval

        self._connections: dict[str, WebSocketConnection] = {}
        self._tasks: dict[str, asyncio.Task[None]] = {}
        self._running = False

    def register_callback(self, callback: NotificationCallback) -> None:
        """Register a callback for notifications."""
        self._callbacks.append(callback)

    async def connect(
        self,
        connection_id: str,
        subscription_id: str,
        websocket_url: str,
        headers: dict[str, str] | None = None,
    ) -> WebSocketConnection:
        """Connect to a WebSocket endpoint for subscription notifications.

        Args:
            connection_id: FHIR connection ID
            subscription_id: Subscription ID
            websocket_url: WebSocket URL to connect to
            headers: Optional headers for connection

        Returns:
            WebSocketConnection object
        """
        conn = WebSocketConnection(
            subscription_id=subscription_id,
            connection_id=connection_id,
            url=websocket_url,
        )

        self._connections[subscription_id] = conn

        # Start connection task
        task = asyncio.create_task(
            self._connection_loop(conn, headers)
        )
        self._tasks[subscription_id] = task

        logger.info(f"Starting WebSocket connection for subscription {subscription_id}")

        return conn

    async def disconnect(self, subscription_id: str) -> None:
        """Disconnect a WebSocket connection.

        Args:
            subscription_id: Subscription ID to disconnect
        """
        if subscription_id in self._tasks:
            task = self._tasks[subscription_id]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del self._tasks[subscription_id]

        if subscription_id in self._connections:
            conn = self._connections[subscription_id]
            if conn.websocket:
                await conn.websocket.close()
            del self._connections[subscription_id]

        logger.info(f"Disconnected WebSocket for subscription {subscription_id}")

    async def _connection_loop(
        self,
        conn: WebSocketConnection,
        headers: dict[str, str] | None = None,
    ) -> None:
        """Main connection loop with reconnection support."""
        while conn.subscription_id in self._connections:
            try:
                extra_headers = headers or {}

                async with websockets.connect(  # type: ignore
                    conn.url,
                    extra_headers=extra_headers,
                    ping_interval=self._ping_interval,
                ) as websocket:
                    conn.websocket = websocket
                    conn.connected = True
                    conn.reconnect_attempts = 0
                    conn.error = None

                    logger.info(f"WebSocket connected: {conn.subscription_id}")

                    await self._receive_loop(conn)

            except asyncio.CancelledError:
                break

            except Exception as e:
                conn.connected = False
                conn.error = str(e)
                conn.reconnect_attempts += 1

                logger.warning(
                    f"WebSocket error for {conn.subscription_id}: {e}, "
                    f"attempt {conn.reconnect_attempts}/{self._max_reconnect}"
                )

                if conn.reconnect_attempts >= self._max_reconnect:
                    logger.error(
                        f"Max reconnect attempts reached for {conn.subscription_id}"
                    )
                    break

                await asyncio.sleep(self._reconnect_delay)

    async def _receive_loop(self, conn: WebSocketConnection) -> None:
        """Receive and process messages from WebSocket."""
        try:
            async for message in conn.websocket:
                conn.last_message_at = datetime.utcnow()

                try:
                    # Parse message as JSON
                    data = json.loads(message)

                    # Check if it's a FHIR Bundle notification
                    if data.get("resourceType") == "Bundle":
                        notification = SubscriptionNotification.from_bundle(data)
                        await self._handle_notification(notification)
                    else:
                        logger.debug(f"Non-bundle WebSocket message: {data}")

                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON from WebSocket: {message[:100]}")
                except Exception as e:
                    logger.error(f"Error processing WebSocket message: {e}")

        except Exception as e:
            logger.error(f"WebSocket receive error: {e}")
            raise

    async def _handle_notification(
        self,
        notification: SubscriptionNotification,
    ) -> None:
        """Handle a received notification."""
        logger.debug(
            f"WebSocket notification: subscription={notification.subscription_id}, "
            f"event={notification.event_number}"
        )

        for callback in self._callbacks:
            try:
                result = callback(notification)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"Callback error: {e}")

    async def send_message(
        self,
        subscription_id: str,
        message: dict[str, Any],
    ) -> bool:
        """Send a message on a WebSocket connection.

        Args:
            subscription_id: Subscription ID
            message: Message to send

        Returns:
            True if sent successfully
        """
        conn = self._connections.get(subscription_id)
        if not conn or not conn.websocket or not conn.connected:
            logger.warning(f"Cannot send to {subscription_id}: not connected")
            return False

        try:
            await conn.websocket.send(json.dumps(message))
            return True
        except Exception as e:
            logger.error(f"Failed to send WebSocket message: {e}")
            return False

    def get_connection(self, subscription_id: str) -> WebSocketConnection | None:
        """Get a WebSocket connection by subscription ID."""
        return self._connections.get(subscription_id)

    def get_all_connections(self) -> list[WebSocketConnection]:
        """Get all WebSocket connections."""
        return list(self._connections.values())

    async def close_all(self) -> None:
        """Close all WebSocket connections."""
        subscription_ids = list(self._connections.keys())
        for sub_id in subscription_ids:
            await self.disconnect(sub_id)


class WebSocketHandler(SubscriptionHandler):
    """Subscription handler using WebSocket transport."""

    def __init__(
        self,
        manager: WebSocketManager | None = None,
    ) -> None:
        """Initialize the WebSocket handler.

        Args:
            manager: WebSocket manager to use
        """
        self._manager = manager or WebSocketManager()

    async def handle_notification(
        self,
        notification: SubscriptionNotification,
    ) -> None:
        """Handle a notification (called by manager)."""
        # This is called by the WebSocket manager
        pass

    async def start(self) -> None:
        """Start the WebSocket handler."""
        logger.info("WebSocket handler started")

    async def stop(self) -> None:
        """Stop the WebSocket handler."""
        await self._manager.close_all()
        logger.info("WebSocket handler stopped")


# Global WebSocket manager instance
try:
    websocket_manager = WebSocketManager()
except ImportError:
    websocket_manager = None  # type: ignore

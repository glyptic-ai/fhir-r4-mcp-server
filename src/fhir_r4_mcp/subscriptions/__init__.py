"""FHIR R4 Subscription support for real-time event notifications."""

from fhir_r4_mcp.subscriptions.handlers import (
    SubscriptionHandler,
    WebhookHandler,
)
from fhir_r4_mcp.subscriptions.manager import (
    SubscriptionConfig,
    SubscriptionManager,
    subscription_manager,
)

__all__ = [
    "SubscriptionConfig",
    "SubscriptionManager",
    "subscription_manager",
    "SubscriptionHandler",
    "WebhookHandler",
]

# Try to import WebSocket support if available
try:
    from fhir_r4_mcp.subscriptions.websocket import (
        WebSocketManager,
        websocket_manager,
    )

    __all__.extend(["WebSocketManager", "websocket_manager"])
except ImportError:
    pass

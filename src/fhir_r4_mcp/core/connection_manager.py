"""Connection manager for FHIR server connections."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from fhir_r4_mcp.core.auth.base import AuthProvider, AuthResult, AuthType
from fhir_r4_mcp.core.auth.smart_backend import SMARTBackendAuth
from fhir_r4_mcp.utils.errors import FHIRAuthError, FHIRConnectionError
from fhir_r4_mcp.utils.logging import get_logger

logger = get_logger(__name__)


class ConnectionStatus(str, Enum):
    """Status of a FHIR connection."""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    TOKEN_EXPIRED = "token_expired"


class VendorType(str, Enum):
    """Supported EHR vendor types."""

    NEXTGEN = "nextgen"
    EPIC = "epic"
    CERNER = "cerner"
    GENERIC = "generic"


@dataclass
class Connection:
    """Represents a connection to a FHIR server."""

    connection_id: str
    base_url: str
    auth_type: AuthType
    vendor: VendorType = VendorType.GENERIC
    status: ConnectionStatus = ConnectionStatus.DISCONNECTED
    auth_result: AuthResult | None = None
    auth_provider: AuthProvider | None = None
    capability_statement: dict[str, Any] | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_used_at: datetime | None = None

    @property
    def is_authenticated(self) -> bool:
        """Check if connection has valid authentication."""
        if self.auth_result is None:
            return False
        return not self.auth_result.is_expired

    def to_dict(self) -> dict[str, Any]:
        """Convert connection to dictionary for API response."""
        return {
            "connection_id": self.connection_id,
            "base_url": self.base_url,
            "auth_type": self.auth_type.value,
            "vendor": self.vendor.value,
            "status": self.status.value,
            "token_expires_at": (
                self.auth_result.expires_at.isoformat()
                if self.auth_result and self.auth_result.expires_at
                else None
            ),
            "created_at": self.created_at.isoformat(),
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
        }


class ConnectionManager:
    """
    Manages connections to multiple FHIR servers.

    This is an in-memory registry of connections. Each connection
    maintains its own authentication state and can be used to
    make requests to the associated FHIR server.
    """

    def __init__(self) -> None:
        """Initialize the connection manager."""
        self._connections: dict[str, Connection] = {}

    def _create_auth_provider(
        self,
        auth_type: AuthType,
        config: dict[str, Any],
    ) -> AuthProvider:
        """
        Create an authentication provider based on type.

        Args:
            auth_type: Type of authentication.
            config: Provider-specific configuration.

        Returns:
            Configured AuthProvider instance.

        Raises:
            ValueError: If auth type is not supported.
        """
        if auth_type == AuthType.SMART_BACKEND:
            return SMARTBackendAuth(config)
        # TODO: Implement other auth providers
        # elif auth_type == AuthType.OAUTH2:
        #     return OAuth2Auth(config)
        # elif auth_type == AuthType.BASIC:
        #     return BasicAuth(config)
        # elif auth_type == AuthType.API_KEY:
        #     return APIKeyAuth(config)
        else:
            raise ValueError(f"Unsupported auth type: {auth_type}")

    async def connect(
        self,
        connection_id: str,
        base_url: str,
        auth_type: str | AuthType,
        vendor: str | VendorType = VendorType.GENERIC,
        **auth_config: Any,
    ) -> Connection:
        """
        Register and authenticate a new FHIR server connection.

        Args:
            connection_id: Unique identifier for this connection.
            base_url: FHIR server base URL.
            auth_type: Authentication type (smart_backend, oauth2, basic, api_key).
            vendor: EHR vendor type (nextgen, epic, cerner, generic).
            **auth_config: Authentication configuration parameters.

        Returns:
            Established Connection object.

        Raises:
            FHIRAuthError: If authentication fails.
            ValueError: If configuration is invalid.
        """
        logger.info(f"Connecting to FHIR server: {connection_id} at {base_url}")

        # Convert string types to enums if needed
        if isinstance(auth_type, str):
            auth_type = AuthType(auth_type)
        if isinstance(vendor, str):
            vendor = VendorType(vendor)

        # Create auth provider
        auth_provider = self._create_auth_provider(auth_type, auth_config)

        # Create connection object
        connection = Connection(
            connection_id=connection_id,
            base_url=base_url.rstrip("/"),
            auth_type=auth_type,
            vendor=vendor,
            auth_provider=auth_provider,
        )

        # Authenticate
        try:
            auth_result = await auth_provider.authenticate()
            connection.auth_result = auth_result
            connection.status = ConnectionStatus.CONNECTED
            logger.info(f"Connection established: {connection_id}")
        except FHIRAuthError as e:
            connection.status = ConnectionStatus.ERROR
            logger.error(f"Authentication failed for {connection_id}: {e}")
            raise

        # Store connection
        self._connections[connection_id] = connection

        return connection

    async def disconnect(self, connection_id: str) -> bool:
        """
        Remove a registered connection.

        Args:
            connection_id: Connection to remove.

        Returns:
            True if connection was removed, False if not found.
        """
        if connection_id in self._connections:
            del self._connections[connection_id]
            logger.info(f"Connection removed: {connection_id}")
            return True
        return False

    def get(self, connection_id: str) -> Connection:
        """
        Get a connection by ID.

        Args:
            connection_id: Connection identifier.

        Returns:
            Connection object.

        Raises:
            FHIRConnectionError: If connection not found.
        """
        if connection_id not in self._connections:
            raise FHIRConnectionError(
                f"Connection not found: {connection_id}",
                connection_id=connection_id,
            )
        return self._connections[connection_id]

    def list_connections(self) -> list[dict[str, Any]]:
        """
        List all active connections.

        Returns:
            List of connection dictionaries with status info.
        """
        return [conn.to_dict() for conn in self._connections.values()]

    async def ensure_authenticated(self, connection_id: str) -> Connection:
        """
        Ensure a connection has valid authentication, refreshing if needed.

        Args:
            connection_id: Connection identifier.

        Returns:
            Connection with valid authentication.

        Raises:
            FHIRConnectionError: If connection not found.
            FHIRAuthError: If authentication cannot be established.
        """
        connection = self.get(connection_id)

        if connection.auth_result and connection.auth_result.is_expired:
            logger.info(f"Token expired for {connection_id}, refreshing...")
            connection.status = ConnectionStatus.TOKEN_EXPIRED

            if connection.auth_provider:
                try:
                    connection.auth_result = await connection.auth_provider.refresh(
                        connection.auth_result
                    )
                    connection.status = ConnectionStatus.CONNECTED
                except FHIRAuthError:
                    # Try full re-authentication
                    connection.auth_result = await connection.auth_provider.authenticate()
                    connection.status = ConnectionStatus.CONNECTED

        connection.last_used_at = datetime.utcnow()
        return connection


# Global connection manager instance
connection_manager = ConnectionManager()

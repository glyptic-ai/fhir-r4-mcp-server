"""Base authentication provider interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class AuthType(str, Enum):
    """Supported authentication types."""

    SMART_BACKEND = "smart_backend"
    OAUTH2 = "oauth2"
    BASIC = "basic"
    API_KEY = "api_key"


@dataclass
class AuthResult:
    """Result of an authentication attempt."""

    access_token: str
    token_type: str = "Bearer"
    expires_at: datetime | None = None
    scope: str | None = None
    refresh_token: str | None = None

    @property
    def is_expired(self) -> bool:
        """Check if the token has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() >= self.expires_at

    @property
    def authorization_header(self) -> str:
        """Get the Authorization header value."""
        return f"{self.token_type} {self.access_token}"


class AuthProvider(ABC):
    """Abstract base class for authentication providers."""

    auth_type: AuthType

    def __init__(self, config: dict[str, Any]) -> None:
        """
        Initialize the auth provider.

        Args:
            config: Provider-specific configuration.
        """
        self.config = config

    @abstractmethod
    async def authenticate(self) -> AuthResult:
        """
        Perform authentication and return credentials.

        Returns:
            AuthResult with access token and metadata.

        Raises:
            FHIRAuthError: If authentication fails.
        """
        ...

    @abstractmethod
    async def refresh(self, auth_result: AuthResult) -> AuthResult:
        """
        Refresh an existing authentication.

        Args:
            auth_result: Previous auth result with refresh token.

        Returns:
            New AuthResult with fresh access token.

        Raises:
            FHIRAuthError: If refresh fails.
        """
        ...

    def validate_config(self) -> None:
        """
        Validate the provider configuration.

        Raises:
            ValueError: If configuration is invalid.
        """
        pass

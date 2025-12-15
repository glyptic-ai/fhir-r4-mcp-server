"""SMART Backend Services authentication provider."""

import time
import uuid
from datetime import datetime, timedelta
from typing import Any

import httpx
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from fhir_r4_mcp.core.auth.base import AuthProvider, AuthResult, AuthType
from fhir_r4_mcp.utils.errors import FHIRAuthError
from fhir_r4_mcp.utils.logging import get_logger

logger = get_logger(__name__)


class SMARTBackendAuth(AuthProvider):
    """
    SMART Backend Services authentication provider.

    Implements the SMART Backend Services authorization flow using
    signed JWT assertions for client authentication.

    See: https://hl7.org/fhir/smart-app-launch/backend-services.html
    """

    auth_type = AuthType.SMART_BACKEND

    def __init__(self, config: dict[str, Any]) -> None:
        """
        Initialize SMART Backend Services auth.

        Config requirements:
            - client_id: Registered client identifier
            - token_endpoint: OAuth2 token endpoint URL
            - private_key_pem: PEM-encoded RSA private key (or path to file)
            - scope: Optional scope string (defaults to "system/*.read")

        Args:
            config: Authentication configuration.
        """
        super().__init__(config)
        self.validate_config()

        self.client_id = config["client_id"]
        self.token_endpoint = config["token_endpoint"]
        self.scope = config.get("scope", "system/*.read")

        # Load private key
        private_key_pem = config["private_key_pem"]
        if private_key_pem.startswith("-----"):
            # It's the actual PEM content
            self._private_key_pem = private_key_pem
        else:
            # It's a file path
            with open(private_key_pem, "r") as f:
                self._private_key_pem = f.read()

    def validate_config(self) -> None:
        """Validate required configuration parameters."""
        required = ["client_id", "token_endpoint", "private_key_pem"]
        missing = [key for key in required if key not in self.config]
        if missing:
            raise ValueError(f"Missing required config keys: {missing}")

    def _create_client_assertion(self) -> str:
        """
        Create a signed JWT client assertion.

        Returns:
            Signed JWT string.
        """
        now = int(time.time())

        payload = {
            "iss": self.client_id,
            "sub": self.client_id,
            "aud": self.token_endpoint,
            "exp": now + 300,  # 5 minutes from now
            "iat": now,
            "jti": str(uuid.uuid4()),
        }

        token = jwt.encode(
            payload,
            self._private_key_pem,
            algorithm="RS384",
        )

        return token

    async def authenticate(self) -> AuthResult:
        """
        Authenticate using SMART Backend Services flow.

        Returns:
            AuthResult with access token.

        Raises:
            FHIRAuthError: If authentication fails.
        """
        logger.info(f"Authenticating with SMART Backend Services: {self.client_id}")

        client_assertion = self._create_client_assertion()

        data = {
            "grant_type": "client_credentials",
            "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
            "client_assertion": client_assertion,
            "scope": self.scope,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.token_endpoint,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=30.0,
                )

                if response.status_code != 200:
                    error_detail = response.text
                    logger.error(f"Authentication failed: {response.status_code} - {error_detail}")
                    raise FHIRAuthError(
                        f"Authentication failed: {response.status_code}",
                        details={"response": error_detail},
                    )

                token_response = response.json()

        except httpx.RequestError as e:
            logger.error(f"Network error during authentication: {e}")
            raise FHIRAuthError(f"Network error: {e}")

        # Calculate expiration time
        expires_in = token_response.get("expires_in", 3600)
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

        logger.info(f"Authentication successful, token expires at {expires_at}")

        return AuthResult(
            access_token=token_response["access_token"],
            token_type=token_response.get("token_type", "Bearer"),
            expires_at=expires_at,
            scope=token_response.get("scope"),
        )

    async def refresh(self, auth_result: AuthResult) -> AuthResult:
        """
        Refresh authentication.

        SMART Backend Services doesn't use refresh tokens - we just
        re-authenticate with a new JWT assertion.

        Args:
            auth_result: Previous auth result (unused for SMART Backend).

        Returns:
            New AuthResult with fresh access token.
        """
        logger.info("Refreshing SMART Backend Services token")
        return await self.authenticate()

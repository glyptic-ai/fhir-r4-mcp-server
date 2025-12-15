"""Async FHIR HTTP client."""

from typing import Any
from urllib.parse import urlencode, urljoin

import httpx

from fhir_r4_mcp.core.connection_manager import Connection, connection_manager
from fhir_r4_mcp.utils.errors import (
    FHIRAuthError,
    FHIRNetworkError,
    FHIRRateLimitError,
    FHIRResourceNotFoundError,
    FHIRServerError,
)
from fhir_r4_mcp.utils.logging import get_logger

logger = get_logger(__name__)

# Default timeout for FHIR requests
DEFAULT_TIMEOUT = 60.0

# Retry configuration
MAX_RETRIES = 3
RETRY_BACKOFF = 1.0  # seconds


class FHIRClient:
    """
    Async HTTP client for FHIR R4 API requests.

    Handles authentication, retries, and error mapping for
    requests to FHIR servers.
    """

    def __init__(
        self,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES,
    ) -> None:
        """
        Initialize the FHIR client.

        Args:
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retry attempts.
        """
        self.timeout = timeout
        self.max_retries = max_retries

    async def _get_headers(self, connection: Connection) -> dict[str, str]:
        """Get request headers including authorization."""
        headers = {
            "Accept": "application/fhir+json",
            "Content-Type": "application/fhir+json",
        }

        if connection.auth_result:
            headers["Authorization"] = connection.auth_result.authorization_header

        return headers

    def _handle_error_response(
        self,
        response: httpx.Response,
        connection_id: str,
    ) -> None:
        """
        Handle error responses from FHIR server.

        Args:
            response: HTTP response object.
            connection_id: Connection identifier for error context.

        Raises:
            FHIRAuthError: For 401/403 responses.
            FHIRResourceNotFoundError: For 404 responses.
            FHIRRateLimitError: For 429 responses.
            FHIRServerError: For 5xx responses.
        """
        status = response.status_code

        if status == 401:
            raise FHIRAuthError(
                "Authentication failed - token may be invalid",
                expired=True,
                details={"connection_id": connection_id},
            )
        elif status == 403:
            raise FHIRAuthError(
                "Access forbidden - insufficient permissions",
                details={"connection_id": connection_id},
            )
        elif status == 404:
            raise FHIRResourceNotFoundError(
                "Resource not found",
                details={"connection_id": connection_id},
            )
        elif status == 429:
            retry_after = response.headers.get("Retry-After")
            raise FHIRRateLimitError(
                "Rate limit exceeded",
                retry_after=int(retry_after) if retry_after else None,
                details={"connection_id": connection_id},
            )
        elif status >= 500:
            raise FHIRServerError(
                f"FHIR server error: {status}",
                status_code=status,
                details={
                    "connection_id": connection_id,
                    "response": response.text[:500],
                },
            )

    async def request(
        self,
        connection_id: str,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Make an HTTP request to a FHIR server.

        Args:
            connection_id: Connection to use.
            method: HTTP method (GET, POST, PUT, DELETE).
            path: Resource path (e.g., "Patient", "Patient/123").
            params: Query parameters.
            json_data: JSON body for POST/PUT requests.

        Returns:
            Parsed JSON response.

        Raises:
            FHIRConnectionError: If connection not found.
            FHIRAuthError: If authentication fails.
            FHIRNetworkError: If network request fails.
            FHIRServerError: If server returns an error.
        """
        # Ensure connection is authenticated
        connection = await connection_manager.ensure_authenticated(connection_id)

        # Build URL
        url = urljoin(connection.base_url + "/", path.lstrip("/"))
        if params:
            # Filter out None values
            filtered_params = {k: v for k, v in params.items() if v is not None}
            if filtered_params:
                url = f"{url}?{urlencode(filtered_params, doseq=True)}"

        headers = await self._get_headers(connection)

        logger.debug(f"FHIR request: {method} {url}")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=json_data,
                )

                if not response.is_success:
                    self._handle_error_response(response, connection_id)

                # Return parsed JSON
                if response.content:
                    return response.json()
                return {}

        except httpx.TimeoutException as e:
            logger.error(f"Request timeout: {url}")
            raise FHIRNetworkError(f"Request timeout: {e}")
        except httpx.RequestError as e:
            logger.error(f"Network error: {e}")
            raise FHIRNetworkError(f"Network error: {e}")

    async def get(
        self,
        connection_id: str,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make a GET request."""
        return await self.request(connection_id, "GET", path, params=params)

    async def post(
        self,
        connection_id: str,
        path: str,
        data: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make a POST request."""
        return await self.request(connection_id, "POST", path, params=params, json_data=data)

    async def put(
        self,
        connection_id: str,
        path: str,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """Make a PUT request."""
        return await self.request(connection_id, "PUT", path, json_data=data)

    async def delete(
        self,
        connection_id: str,
        path: str,
    ) -> dict[str, Any]:
        """Make a DELETE request."""
        return await self.request(connection_id, "DELETE", path)

    async def search(
        self,
        connection_id: str,
        resource_type: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Search for FHIR resources.

        Args:
            connection_id: Connection to use.
            resource_type: FHIR resource type (e.g., "Patient").
            params: Search parameters.

        Returns:
            FHIR Bundle containing search results.
        """
        return await self.get(connection_id, resource_type, params=params)

    async def read(
        self,
        connection_id: str,
        resource_type: str,
        resource_id: str,
    ) -> dict[str, Any]:
        """
        Read a specific FHIR resource.

        Args:
            connection_id: Connection to use.
            resource_type: FHIR resource type.
            resource_id: Resource identifier.

        Returns:
            FHIR resource.
        """
        return await self.get(connection_id, f"{resource_type}/{resource_id}")


# Global client instance
fhir_client = FHIRClient()

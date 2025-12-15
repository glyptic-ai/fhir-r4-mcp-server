"""Error classes for FHIR R4 MCP Server."""

from typing import Any


class FHIRError(Exception):
    """Base exception for all FHIR-related errors."""

    code: str = "FHIR_ERROR"
    recoverable: bool = False

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        suggestion: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.suggestion = suggestion

    def to_dict(self) -> dict[str, Any]:
        """Convert error to dictionary for API response."""
        result: dict[str, Any] = {
            "code": self.code,
            "message": self.message,
            "recoverable": self.recoverable,
        }
        if self.details:
            result["details"] = self.details
        if self.suggestion:
            result["suggestion"] = self.suggestion
        return result


class FHIRConnectionError(FHIRError):
    """Error when connection to FHIR server fails or is not found."""

    code = "FHIR_CONNECTION_NOT_FOUND"
    recoverable = True

    def __init__(
        self,
        message: str = "Connection not found",
        connection_id: str | None = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if connection_id:
            details["connection_id"] = connection_id
        super().__init__(
            message,
            details=details,
            suggestion="Call fhir_connect to establish a connection",
            **kwargs,
        )


class FHIRAuthError(FHIRError):
    """Error when authentication fails or token expires."""

    code = "FHIR_AUTH_FAILED"
    recoverable = True

    def __init__(
        self,
        message: str = "Authentication failed",
        expired: bool = False,
        **kwargs: Any,
    ) -> None:
        if expired:
            self.code = "FHIR_AUTH_EXPIRED"
        super().__init__(
            message,
            suggestion="Call fhir_connect to re-authenticate",
            **kwargs,
        )


class FHIRResourceNotFoundError(FHIRError):
    """Error when a requested FHIR resource does not exist."""

    code = "FHIR_RESOURCE_NOT_FOUND"
    recoverable = False

    def __init__(
        self,
        message: str = "Resource not found",
        resource_type: str | None = None,
        resource_id: str | None = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id
        super().__init__(message, details=details, **kwargs)


class FHIRValidationError(FHIRError):
    """Error when request parameters are invalid."""

    code = "FHIR_INVALID_SEARCH"
    recoverable = False

    def __init__(
        self,
        message: str = "Invalid search parameters",
        **kwargs: Any,
    ) -> None:
        super().__init__(message, **kwargs)


class FHIRRateLimitError(FHIRError):
    """Error when FHIR server rate limit is exceeded."""

    code = "FHIR_RATE_LIMITED"
    recoverable = True

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int | None = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if retry_after:
            details["retry_after_seconds"] = retry_after
        super().__init__(
            message,
            details=details,
            suggestion=f"Wait {retry_after or 'a moment'} before retrying",
            **kwargs,
        )


class FHIROperationNotSupportedError(FHIRError):
    """Error when the requested operation is not supported by the server."""

    code = "FHIR_OPERATION_NOT_SUPPORTED"
    recoverable = False

    def __init__(
        self,
        message: str = "Operation not supported",
        operation: str | None = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if operation:
            details["operation"] = operation
        super().__init__(
            message,
            details=details,
            suggestion="Check fhir_capability_statement for supported operations",
            **kwargs,
        )


class FHIRBulkExportError(FHIRError):
    """Error during bulk export operations."""

    code = "FHIR_BULK_EXPORT_FAILED"
    recoverable = True  # May be recoverable depending on the cause

    def __init__(
        self,
        message: str = "Bulk export failed",
        job_id: str | None = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if job_id:
            details["job_id"] = job_id
        super().__init__(message, details=details, **kwargs)


class FHIRNetworkError(FHIRError):
    """Error when network communication fails."""

    code = "FHIR_NETWORK_ERROR"
    recoverable = True

    def __init__(
        self,
        message: str = "Network error",
        **kwargs: Any,
    ) -> None:
        super().__init__(
            message,
            suggestion="Check network connectivity and retry",
            **kwargs,
        )


class FHIRServerError(FHIRError):
    """Error when FHIR server returns a 5xx error."""

    code = "FHIR_SERVER_ERROR"
    recoverable = True  # May be recoverable on retry

    def __init__(
        self,
        message: str = "FHIR server error",
        status_code: int | None = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if status_code:
            details["status_code"] = status_code
        super().__init__(
            message,
            details=details,
            suggestion="The FHIR server may be temporarily unavailable. Try again later.",
            **kwargs,
        )

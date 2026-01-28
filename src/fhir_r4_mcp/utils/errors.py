"""Error classes for FHIR R4 MCP Server."""

from typing import Any


# FHIR OperationOutcome issue type codes
# See: https://hl7.org/fhir/R4/valueset-issue-type.html
class IssueType:
    """FHIR OperationOutcome issue type codes."""

    # Processing issues
    INVALID = "invalid"
    STRUCTURE = "structure"
    REQUIRED = "required"
    VALUE = "value"
    INVARIANT = "invariant"
    SECURITY = "security"
    LOGIN = "login"
    UNKNOWN = "unknown"
    EXPIRED = "expired"
    FORBIDDEN = "forbidden"
    SUPPRESSED = "suppressed"
    PROCESSING = "processing"
    NOT_SUPPORTED = "not-supported"
    DUPLICATE = "duplicate"
    MULTIPLE_MATCHES = "multiple-matches"
    NOT_FOUND = "not-found"
    DELETED = "deleted"
    TOO_LONG = "too-long"
    CODE_INVALID = "code-invalid"
    EXTENSION = "extension"
    TOO_COSTLY = "too-costly"
    BUSINESS_RULE = "business-rule"
    CONFLICT = "conflict"
    TRANSIENT = "transient"
    LOCK_ERROR = "lock-error"
    NO_STORE = "no-store"
    EXCEPTION = "exception"
    TIMEOUT = "timeout"
    INCOMPLETE = "incomplete"
    THROTTLED = "throttled"
    INFORMATIONAL = "informational"


# FHIR OperationOutcome severity codes
class IssueSeverity:
    """FHIR OperationOutcome severity codes."""

    FATAL = "fatal"
    ERROR = "error"
    WARNING = "warning"
    INFORMATION = "information"


class FHIRError(Exception):
    """Base exception for all FHIR-related errors."""

    code: str = "FHIR_ERROR"
    recoverable: bool = False
    fhir_issue_type: str = IssueType.PROCESSING
    fhir_severity: str = IssueSeverity.ERROR
    http_status: int = 500

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

    def to_operation_outcome(self) -> dict[str, Any]:
        """
        Convert error to FHIR OperationOutcome resource.

        Returns a valid FHIR R4 OperationOutcome resource that can be
        returned as an error response per FHIR specification.

        See: https://hl7.org/fhir/R4/operationoutcome.html
        """
        issue: dict[str, Any] = {
            "severity": self.fhir_severity,
            "code": self.fhir_issue_type,
            "diagnostics": self.message,
        }

        # Add details if available
        if self.suggestion:
            issue["details"] = {
                "text": self.suggestion,
            }

        # Add extension for error code mapping
        if self.details:
            issue["extension"] = [
                {
                    "url": "https://fhir-r4-mcp.io/StructureDefinition/error-details",
                    "valueString": str(self.details),
                }
            ]

        return {
            "resourceType": "OperationOutcome",
            "issue": [issue],
        }


class FHIRConnectionError(FHIRError):
    """Error when connection to FHIR server fails or is not found."""

    code = "FHIR_CONNECTION_NOT_FOUND"
    recoverable = True
    fhir_issue_type = IssueType.NOT_FOUND
    fhir_severity = IssueSeverity.ERROR
    http_status = 404

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
    fhir_issue_type = IssueType.SECURITY
    fhir_severity = IssueSeverity.ERROR
    http_status = 401

    def __init__(
        self,
        message: str = "Authentication failed",
        expired: bool = False,
        **kwargs: Any,
    ) -> None:
        if expired:
            self.code = "FHIR_AUTH_EXPIRED"
            self.fhir_issue_type = IssueType.EXPIRED
        super().__init__(
            message,
            suggestion="Call fhir_connect to re-authenticate",
            **kwargs,
        )


class FHIRResourceNotFoundError(FHIRError):
    """Error when a requested FHIR resource does not exist."""

    code = "FHIR_RESOURCE_NOT_FOUND"
    recoverable = False
    fhir_issue_type = IssueType.NOT_FOUND
    fhir_severity = IssueSeverity.ERROR
    http_status = 404

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
    """Error when request parameters or resource data are invalid."""

    code = "FHIR_VALIDATION_ERROR"
    recoverable = False
    fhir_issue_type = IssueType.INVALID
    fhir_severity = IssueSeverity.ERROR
    http_status = 400

    def __init__(
        self,
        message: str = "Validation failed",
        field: str | None = None,
        value: Any | None = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)
        super().__init__(message, details=details, **kwargs)


class FHIRRateLimitError(FHIRError):
    """Error when FHIR server rate limit is exceeded."""

    code = "FHIR_RATE_LIMITED"
    recoverable = True
    fhir_issue_type = IssueType.THROTTLED
    fhir_severity = IssueSeverity.ERROR
    http_status = 429

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
    fhir_issue_type = IssueType.NOT_SUPPORTED
    fhir_severity = IssueSeverity.ERROR
    http_status = 501

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
    recoverable = True
    fhir_issue_type = IssueType.PROCESSING
    fhir_severity = IssueSeverity.ERROR
    http_status = 500

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
    fhir_issue_type = IssueType.TRANSIENT
    fhir_severity = IssueSeverity.ERROR
    http_status = 503

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
    recoverable = True
    fhir_issue_type = IssueType.EXCEPTION
    fhir_severity = IssueSeverity.ERROR
    http_status = 502

    def __init__(
        self,
        message: str = "FHIR server error",
        status_code: int | None = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if status_code:
            details["status_code"] = status_code
            self.http_status = status_code
        super().__init__(
            message,
            details=details,
            suggestion="The FHIR server may be temporarily unavailable. Try again later.",
            **kwargs,
        )


class FHIRRequiredFieldError(FHIRValidationError):
    """Error when a required FHIR field is missing."""

    code = "FHIR_REQUIRED_FIELD_MISSING"
    fhir_issue_type = IssueType.REQUIRED
    http_status = 422

    def __init__(
        self,
        message: str = "Required field missing",
        field: str | None = None,
        resource_type: str | None = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if resource_type:
            details["resource_type"] = resource_type
        super().__init__(
            message,
            field=field,
            details=details,
            suggestion=f"Provide a value for the required field: {field}",
            **kwargs,
        )


class FHIRValueSetError(FHIRValidationError):
    """Error when a value is not in the required value set."""

    code = "FHIR_VALUE_SET_ERROR"
    fhir_issue_type = IssueType.CODE_INVALID
    http_status = 422

    def __init__(
        self,
        message: str = "Value not in allowed set",
        field: str | None = None,
        value: Any | None = None,
        allowed_values: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if allowed_values:
            details["allowed_values"] = allowed_values
        super().__init__(
            message,
            field=field,
            value=value,
            details=details,
            suggestion=f"Use one of the allowed values: {', '.join(allowed_values or [])}",
            **kwargs,
        )

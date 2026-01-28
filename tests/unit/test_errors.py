"""Unit tests for error classes."""

import pytest

from fhir_r4_mcp.utils.errors import (
    FHIRAuthError,
    FHIRConnectionError,
    FHIRError,
    FHIRResourceNotFoundError,
    FHIRValidationError,
    FHIRRequiredFieldError,
    FHIRValueSetError,
    FHIRRateLimitError,
    FHIRServerError,
    FHIRNetworkError,
    FHIROperationNotSupportedError,
    IssueType,
    IssueSeverity,
)


class TestFHIRErrors:
    """Tests for FHIR error classes."""

    def test_base_error(self):
        """Test base FHIRError."""
        error = FHIRError("Test error", details={"key": "value"}, suggestion="Try again")

        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.details == {"key": "value"}
        assert error.suggestion == "Try again"
        assert error.code == "FHIR_ERROR"
        assert error.recoverable is False

    def test_base_error_to_dict(self):
        """Test converting error to dictionary."""
        error = FHIRError("Test error", details={"key": "value"}, suggestion="Try again")
        result = error.to_dict()

        assert result["code"] == "FHIR_ERROR"
        assert result["message"] == "Test error"
        assert result["recoverable"] is False
        assert result["details"] == {"key": "value"}
        assert result["suggestion"] == "Try again"

    def test_connection_error(self):
        """Test FHIRConnectionError."""
        error = FHIRConnectionError("Not found", connection_id="test-conn")

        assert error.code == "FHIR_CONNECTION_NOT_FOUND"
        assert error.recoverable is True
        assert error.details["connection_id"] == "test-conn"
        assert "fhir_connect" in error.suggestion

    def test_auth_error(self):
        """Test FHIRAuthError."""
        error = FHIRAuthError("Auth failed")

        assert error.code == "FHIR_AUTH_FAILED"
        assert error.recoverable is True

    def test_auth_error_expired(self):
        """Test FHIRAuthError with expired flag."""
        error = FHIRAuthError("Token expired", expired=True)

        assert error.code == "FHIR_AUTH_EXPIRED"
        assert error.recoverable is True

    def test_resource_not_found_error(self):
        """Test FHIRResourceNotFoundError."""
        error = FHIRResourceNotFoundError(
            "Patient not found",
            resource_type="Patient",
            resource_id="123",
        )

        assert error.code == "FHIR_RESOURCE_NOT_FOUND"
        assert error.recoverable is False
        assert error.details["resource_type"] == "Patient"
        assert error.details["resource_id"] == "123"

    def test_validation_error(self):
        """Test FHIRValidationError."""
        error = FHIRValidationError("Invalid date format", field="birthdate", value="not-a-date")

        assert error.code == "FHIR_VALIDATION_ERROR"
        assert error.recoverable is False
        assert error.http_status == 400
        assert error.details["field"] == "birthdate"
        assert error.details["value"] == "not-a-date"


class TestOperationOutcome:
    """Tests for FHIR OperationOutcome generation."""

    def test_base_error_operation_outcome(self):
        """Test OperationOutcome generation from base error."""
        error = FHIRError("Test error", suggestion="Try again")
        outcome = error.to_operation_outcome()

        assert outcome["resourceType"] == "OperationOutcome"
        assert len(outcome["issue"]) == 1
        assert outcome["issue"][0]["severity"] == IssueSeverity.ERROR
        assert outcome["issue"][0]["code"] == IssueType.PROCESSING
        assert outcome["issue"][0]["diagnostics"] == "Test error"
        assert outcome["issue"][0]["details"]["text"] == "Try again"

    def test_resource_not_found_operation_outcome(self):
        """Test OperationOutcome for not found error."""
        error = FHIRResourceNotFoundError(
            "Patient/123 not found",
            resource_type="Patient",
            resource_id="123",
        )
        outcome = error.to_operation_outcome()

        assert outcome["resourceType"] == "OperationOutcome"
        assert outcome["issue"][0]["severity"] == IssueSeverity.ERROR
        assert outcome["issue"][0]["code"] == IssueType.NOT_FOUND
        assert "Patient/123" in outcome["issue"][0]["diagnostics"]

    def test_auth_error_operation_outcome(self):
        """Test OperationOutcome for auth error."""
        error = FHIRAuthError("Token expired", expired=True)
        outcome = error.to_operation_outcome()

        assert outcome["issue"][0]["code"] == IssueType.EXPIRED

    def test_validation_error_operation_outcome(self):
        """Test OperationOutcome for validation error."""
        error = FHIRValidationError("Invalid status value", field="status", value="bad")
        outcome = error.to_operation_outcome()

        assert outcome["issue"][0]["code"] == IssueType.INVALID
        assert outcome["issue"][0]["severity"] == IssueSeverity.ERROR

    def test_rate_limit_operation_outcome(self):
        """Test OperationOutcome for rate limit error."""
        error = FHIRRateLimitError("Rate limit exceeded", retry_after=60)
        outcome = error.to_operation_outcome()

        assert outcome["issue"][0]["code"] == IssueType.THROTTLED
        assert error.http_status == 429

    def test_server_error_operation_outcome(self):
        """Test OperationOutcome for server error."""
        error = FHIRServerError("Internal server error", status_code=500)
        outcome = error.to_operation_outcome()

        assert outcome["issue"][0]["code"] == IssueType.EXCEPTION
        assert error.http_status == 500

    def test_required_field_error(self):
        """Test FHIRRequiredFieldError."""
        error = FHIRRequiredFieldError(
            "Observation.status is required",
            field="status",
            resource_type="Observation",
        )

        assert error.code == "FHIR_REQUIRED_FIELD_MISSING"
        assert error.fhir_issue_type == IssueType.REQUIRED
        assert error.http_status == 422
        assert error.details["field"] == "status"
        assert error.details["resource_type"] == "Observation"

    def test_value_set_error(self):
        """Test FHIRValueSetError."""
        error = FHIRValueSetError(
            "Invalid status 'bad'",
            field="status",
            value="bad",
            allowed_values=["active", "completed"],
        )

        assert error.code == "FHIR_VALUE_SET_ERROR"
        assert error.fhir_issue_type == IssueType.CODE_INVALID
        assert error.http_status == 422
        assert error.details["allowed_values"] == ["active", "completed"]


class TestHTTPStatusCodes:
    """Tests for HTTP status code mapping."""

    def test_connection_error_status(self):
        """Test connection error returns 404."""
        error = FHIRConnectionError("Connection not found")
        assert error.http_status == 404

    def test_auth_error_status(self):
        """Test auth error returns 401."""
        error = FHIRAuthError("Unauthorized")
        assert error.http_status == 401

    def test_validation_error_status(self):
        """Test validation error returns 400."""
        error = FHIRValidationError("Invalid input")
        assert error.http_status == 400

    def test_not_found_error_status(self):
        """Test not found error returns 404."""
        error = FHIRResourceNotFoundError("Not found")
        assert error.http_status == 404

    def test_rate_limit_error_status(self):
        """Test rate limit error returns 429."""
        error = FHIRRateLimitError("Too many requests")
        assert error.http_status == 429

    def test_not_supported_error_status(self):
        """Test not supported error returns 501."""
        error = FHIROperationNotSupportedError("Not implemented")
        assert error.http_status == 501

    def test_network_error_status(self):
        """Test network error returns 503."""
        error = FHIRNetworkError("Connection failed")
        assert error.http_status == 503

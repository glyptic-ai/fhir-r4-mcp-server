"""Unit tests for error classes."""

import pytest

from fhir_r4_mcp.utils.errors import (
    FHIRAuthError,
    FHIRConnectionError,
    FHIRError,
    FHIRResourceNotFoundError,
    FHIRValidationError,
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
        error = FHIRValidationError("Invalid date format")

        assert error.code == "FHIR_INVALID_SEARCH"
        assert error.recoverable is False

"""Unit tests for response processor."""

import pytest

from fhir_r4_mcp.core.response_processor import ResponseProcessor


class TestResponseProcessor:
    """Tests for ResponseProcessor class."""

    def test_create_success_response(self):
        """Test creating a success response."""
        data = {"resourceType": "Patient", "id": "123"}
        response = ResponseProcessor.create_success_response(
            data=data,
            connection_id="test-conn",
            duration_ms=100,
        )

        assert response["success"] is True
        assert response["data"] == data
        assert response["metadata"]["connection_id"] == "test-conn"
        assert response["metadata"]["duration_ms"] == 100
        assert "request_id" in response["metadata"]
        assert "timestamp" in response["metadata"]

    def test_create_success_response_with_pagination(self):
        """Test creating a success response with pagination."""
        pagination = {"total": 100, "returned": 10, "next_url": "http://example.com/next"}
        response = ResponseProcessor.create_success_response(
            data=[],
            connection_id="test-conn",
            pagination=pagination,
        )

        assert response["metadata"]["pagination"] == pagination

    def test_create_error_response(self):
        """Test creating an error response."""
        error = ValueError("Test error")
        response = ResponseProcessor.create_error_response(
            error=error,
            connection_id="test-conn",
        )

        assert response["success"] is False
        assert response["error"]["message"] == "Test error"
        assert response["metadata"]["connection_id"] == "test-conn"

    def test_extract_bundle_entries(self, sample_bundle):
        """Test extracting entries from a bundle."""
        entries = ResponseProcessor.extract_bundle_entries(sample_bundle)

        assert len(entries) == 1
        assert entries[0]["resourceType"] == "Patient"

    def test_extract_bundle_entries_non_bundle(self, sample_patient):
        """Test extracting entries from a non-bundle resource."""
        entries = ResponseProcessor.extract_bundle_entries(sample_patient)

        assert len(entries) == 1
        assert entries[0] == sample_patient

    def test_extract_pagination(self, sample_bundle):
        """Test extracting pagination from a bundle."""
        pagination = ResponseProcessor.extract_pagination(sample_bundle)

        assert pagination["total"] == 1
        assert pagination["returned"] == 1

    def test_extract_pagination_with_next_link(self):
        """Test extracting pagination with next link."""
        bundle = {
            "resourceType": "Bundle",
            "type": "searchset",
            "total": 100,
            "entry": [{"resource": {}}] * 10,
            "link": [
                {"relation": "self", "url": "http://example.com/Patient"},
                {"relation": "next", "url": "http://example.com/Patient?page=2"},
            ],
        }
        pagination = ResponseProcessor.extract_pagination(bundle)

        assert pagination["total"] == 100
        assert pagination["returned"] == 10
        assert pagination["next_url"] == "http://example.com/Patient?page=2"

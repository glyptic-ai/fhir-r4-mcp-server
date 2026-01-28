"""Response processor for FHIR API responses."""

import uuid
from datetime import datetime
from typing import Any

from fhir_r4_mcp.utils.logging import get_logger

logger = get_logger(__name__)


class ResponseProcessor:
    """
    Processes FHIR API responses into standardized format.

    Handles Bundle parsing, pagination, and response formatting
    for consistent API responses.
    """

    @staticmethod
    def create_success_response(
        data: Any,
        connection_id: str,
        duration_ms: int | None = None,
        pagination: dict[str, Any] | None = None,
        http_status: int = 200,
    ) -> dict[str, Any]:
        """
        Create a standardized success response.

        Args:
            data: FHIR resource or array of resources.
            connection_id: Connection identifier.
            duration_ms: Request duration in milliseconds.
            pagination: Pagination metadata.
            http_status: HTTP status code (200 for read/search, 201 for create, 204 for delete).

        Returns:
            Standardized response dictionary.
        """
        response: dict[str, Any] = {
            "success": True,
            "data": data,
            "metadata": {
                "connection_id": connection_id,
                "request_id": f"req_{uuid.uuid4().hex[:12]}",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "http_status": http_status,
            },
        }

        if duration_ms is not None:
            response["metadata"]["duration_ms"] = duration_ms

        if pagination:
            response["metadata"]["pagination"] = pagination

        return response

    @staticmethod
    def create_error_response(
        error: Exception,
        connection_id: str | None = None,
        include_operation_outcome: bool = True,
    ) -> dict[str, Any]:
        """
        Create a standardized error response with FHIR OperationOutcome.

        Args:
            error: Exception that occurred.
            connection_id: Connection identifier (if available).
            include_operation_outcome: Whether to include OperationOutcome resource.

        Returns:
            Standardized error response dictionary with OperationOutcome.
        """
        from fhir_r4_mcp.utils.errors import FHIRError, IssueType, IssueSeverity

        response: dict[str, Any] = {
            "success": False,
            "metadata": {
                "request_id": f"req_{uuid.uuid4().hex[:12]}",
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
        }

        if connection_id:
            response["metadata"]["connection_id"] = connection_id

        if isinstance(error, FHIRError):
            response["error"] = error.to_dict()
            response["metadata"]["http_status"] = error.http_status
            if include_operation_outcome:
                response["operation_outcome"] = error.to_operation_outcome()
        else:
            response["error"] = {
                "code": "FHIR_ERROR",
                "message": str(error),
                "recoverable": False,
            }
            response["metadata"]["http_status"] = 500
            if include_operation_outcome:
                response["operation_outcome"] = {
                    "resourceType": "OperationOutcome",
                    "issue": [
                        {
                            "severity": IssueSeverity.ERROR,
                            "code": IssueType.EXCEPTION,
                            "diagnostics": str(error),
                        }
                    ],
                }

        return response

    @staticmethod
    def extract_bundle_entries(bundle: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Extract resource entries from a FHIR Bundle.

        Args:
            bundle: FHIR Bundle resource.

        Returns:
            List of resources from bundle entries.
        """
        if bundle.get("resourceType") != "Bundle":
            # Not a bundle, return as single-item list
            return [bundle]

        entries = bundle.get("entry", [])
        return [entry.get("resource", entry) for entry in entries]

    @staticmethod
    def extract_pagination(bundle: dict[str, Any]) -> dict[str, Any]:
        """
        Extract pagination information from a FHIR Bundle.

        Args:
            bundle: FHIR Bundle resource.

        Returns:
            Pagination metadata dictionary.
        """
        pagination: dict[str, Any] = {}

        if bundle.get("resourceType") != "Bundle":
            return pagination

        # Total count
        if "total" in bundle:
            pagination["total"] = bundle["total"]

        # Count returned
        entries = bundle.get("entry", [])
        pagination["returned"] = len(entries)

        # Next page URL
        links = bundle.get("link", [])
        for link in links:
            if link.get("relation") == "next":
                pagination["next_url"] = link.get("url")
                break

        return pagination

    @staticmethod
    def parse_search_result(
        bundle: dict[str, Any],
        connection_id: str,
        duration_ms: int | None = None,
    ) -> dict[str, Any]:
        """
        Parse a FHIR search result bundle into standardized response.

        Args:
            bundle: FHIR Bundle from search operation.
            connection_id: Connection identifier.
            duration_ms: Request duration.

        Returns:
            Standardized response with parsed data and pagination.
        """
        pagination = ResponseProcessor.extract_pagination(bundle)

        return ResponseProcessor.create_success_response(
            data=bundle,  # Return raw FHIR Bundle
            connection_id=connection_id,
            duration_ms=duration_ms,
            pagination=pagination if pagination else None,
        )

    @staticmethod
    def parse_resource(
        resource: dict[str, Any],
        connection_id: str,
        duration_ms: int | None = None,
    ) -> dict[str, Any]:
        """
        Parse a single FHIR resource into standardized response.

        Args:
            resource: FHIR resource.
            connection_id: Connection identifier.
            duration_ms: Request duration.

        Returns:
            Standardized response with resource data.
        """
        return ResponseProcessor.create_success_response(
            data=resource,  # Return raw FHIR resource
            connection_id=connection_id,
            duration_ms=duration_ms,
        )


# Global processor instance
response_processor = ResponseProcessor()

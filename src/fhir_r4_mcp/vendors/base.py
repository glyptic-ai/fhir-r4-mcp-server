"""Base vendor profile interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class VendorQuirks:
    """Vendor-specific quirks and behaviors."""

    # Date format used by the vendor
    date_format: str = "YYYY-MM-DD"

    # Pagination style
    pagination_style: str = "next_link"  # or "offset", "page"

    # Bulk export status header
    bulk_status_header: str | None = None

    # Whether to include 'aud' claim in JWT
    requires_aud_claim: bool = False

    # Whether documents are inline or require binary fetch
    document_binary_inline: bool = True

    # Maximum search results per request
    search_count_max: int = 100

    # Patient search endpoint (if custom)
    patient_search_endpoint: str | None = None

    # Additional quirks as key-value pairs
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class BulkExportConfig:
    """Configuration for bulk export operations."""

    # Base URL for bulk FHIR operations (if different from main base_url)
    bulk_base_url: str | None = None

    # Maximum patients per group
    max_group_size: int = 1000

    # Maximum groups per practice
    max_groups_per_practice: int = 1000

    # Supported resource types for bulk export
    supported_types: list[str] = field(default_factory=list)

    # Whether bulk export is supported at all
    supported: bool = True


class VendorProfile(ABC):
    """
    Abstract base class for EHR vendor profiles.

    Vendor profiles encapsulate EHR-specific behaviors, endpoints,
    and quirks to provide a consistent interface across different
    FHIR server implementations.
    """

    # Vendor identifier
    vendor_id: str

    # Human-readable vendor name
    vendor_name: str

    # Default authentication type
    default_auth_type: str = "smart_backend"

    def __init__(self) -> None:
        """Initialize the vendor profile."""
        self._quirks = self._get_quirks()
        self._bulk_config = self._get_bulk_config()

    @abstractmethod
    def _get_quirks(self) -> VendorQuirks:
        """Get vendor-specific quirks."""
        ...

    @abstractmethod
    def _get_bulk_config(self) -> BulkExportConfig:
        """Get bulk export configuration."""
        ...

    @property
    def quirks(self) -> VendorQuirks:
        """Get vendor quirks."""
        return self._quirks

    @property
    def bulk_config(self) -> BulkExportConfig:
        """Get bulk export configuration."""
        return self._bulk_config

    def get_token_endpoint(self, base_url: str) -> str:
        """
        Get the OAuth token endpoint for this vendor.

        Args:
            base_url: FHIR server base URL.

        Returns:
            Token endpoint URL.
        """
        # Default: standard OAuth2 token endpoint
        return f"{base_url.rstrip('/')}/oauth2/token"

    def get_patient_search_path(self) -> str:
        """
        Get the path for patient search operations.

        Returns:
            Patient search endpoint path.
        """
        if self._quirks.patient_search_endpoint:
            return self._quirks.patient_search_endpoint
        return "Patient"

    def get_bulk_export_path(self, export_type: str, group_id: str | None = None) -> str:
        """
        Get the path for bulk export operations.

        Args:
            export_type: Type of export (system, patient, group).
            group_id: Group ID for group exports.

        Returns:
            Bulk export endpoint path.
        """
        if export_type == "system":
            return "$export"
        elif export_type == "patient":
            return "Patient/$export"
        elif export_type == "group" and group_id:
            return f"Group/{group_id}/$export"
        else:
            raise ValueError(f"Invalid export type: {export_type}")

    def transform_search_params(
        self,
        resource_type: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Transform search parameters for vendor-specific requirements.

        Args:
            resource_type: FHIR resource type.
            params: Original search parameters.

        Returns:
            Transformed parameters.
        """
        # Default: no transformation
        return params

    def transform_response(
        self,
        resource_type: str,
        response: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Transform response for vendor-specific normalization.

        Args:
            resource_type: FHIR resource type.
            response: Original response.

        Returns:
            Transformed response.
        """
        # Default: no transformation
        return response

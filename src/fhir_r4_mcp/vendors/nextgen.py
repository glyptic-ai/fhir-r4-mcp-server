"""NextGen Healthcare vendor profile."""

from typing import Any

from fhir_r4_mcp.vendors.base import BulkExportConfig, VendorProfile, VendorQuirks


class NextGenProfile(VendorProfile):
    """
    NextGen Healthcare vendor profile.

    Handles NextGen-specific quirks and endpoints for their FHIR R4
    implementation, including Bulk FHIR API support.

    Reference:
    - https://developer.nextgen.com/
    - Bulk API: https://fhir.meditouchehr.com/api/bulkfhir/r4
    """

    vendor_id = "nextgen"
    vendor_name = "NextGen Healthcare"
    default_auth_type = "smart_backend"

    # NextGen-specific endpoints
    BULK_FHIR_BASE = "https://fhir.meditouchehr.com/api/bulkfhir/r4"

    def _get_quirks(self) -> VendorQuirks:
        """Get NextGen-specific quirks."""
        return VendorQuirks(
            date_format="YYYY-MM-DD",
            pagination_style="next_link",
            bulk_status_header="X-Progress",
            requires_aud_claim=False,
            document_binary_inline=False,  # Binary references need separate fetch
            search_count_max=1000,
            patient_search_endpoint="$patient-search",
            extra={
                "supports_uscdi_v1": True,
                "non_ehi_routes_available": False,
            },
        )

    def _get_bulk_config(self) -> BulkExportConfig:
        """Get NextGen bulk export configuration."""
        return BulkExportConfig(
            bulk_base_url=self.BULK_FHIR_BASE,
            max_group_size=1000,
            max_groups_per_practice=1000,
            supported=True,
            supported_types=[
                "Patient",
                "AllergyIntolerance",
                "CarePlan",
                "Condition",
                "DiagnosticReport",
                "DocumentReference",
                "MedicationRequest",
                "Observation",
            ],
        )

    def get_token_endpoint(self, base_url: str) -> str:
        """Get NextGen OAuth token endpoint."""
        # NextGen uses standard OAuth2 token endpoint
        return f"{base_url.rstrip('/')}/oauth2/token"

    def get_patient_search_path(self) -> str:
        """Get NextGen patient search endpoint."""
        # NextGen uses custom $patient-search operation
        return "$patient-search"

    def transform_search_params(
        self,
        resource_type: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Transform search parameters for NextGen-specific requirements.

        NextGen has some specific parameter handling requirements.
        """
        transformed = params.copy()

        # NextGen-specific transformations can be added here
        # For example, handling date formats or parameter naming

        return transformed

    def transform_response(
        self,
        resource_type: str,
        response: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Transform response for NextGen-specific normalization.

        Handles any NextGen-specific response formats that need
        normalization to standard FHIR R4.
        """
        # Currently no transformations needed - NextGen returns standard FHIR R4
        return response

"""Generic FHIR R4 vendor profile."""

from fhir_r4_mcp.vendors.base import BulkExportConfig, VendorProfile, VendorQuirks


class GenericProfile(VendorProfile):
    """
    Generic FHIR R4 vendor profile.

    Assumes strict FHIR R4 compliance with no vendor-specific quirks.
    Use this profile when connecting to unknown or standards-compliant
    FHIR servers.
    """

    vendor_id = "generic"
    vendor_name = "Generic FHIR R4"
    default_auth_type = "smart_backend"

    def _get_quirks(self) -> VendorQuirks:
        """Get default FHIR R4 quirks."""
        return VendorQuirks(
            date_format="YYYY-MM-DD",
            pagination_style="next_link",
            document_binary_inline=True,
            search_count_max=100,
        )

    def _get_bulk_config(self) -> BulkExportConfig:
        """Get default bulk export configuration."""
        return BulkExportConfig(
            max_group_size=1000,
            max_groups_per_practice=1000,
            supported=True,
            supported_types=[
                "Patient",
                "AllergyIntolerance",
                "CarePlan",
                "CareTeam",
                "Condition",
                "Device",
                "DiagnosticReport",
                "DocumentReference",
                "Encounter",
                "Goal",
                "Immunization",
                "Location",
                "Medication",
                "MedicationRequest",
                "MedicationStatement",
                "Observation",
                "Organization",
                "Practitioner",
                "Procedure",
                "Provenance",
                "ServiceRequest",
            ],
        )

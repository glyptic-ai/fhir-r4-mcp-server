"""FHIR R4 Value Set definitions and validation.

This module contains the required value sets for FHIR R4 resources
and provides validation functions to ensure values conform to the spec.

See: https://hl7.org/fhir/R4/terminologies-valuesets.html
"""

from typing import Any

from fhir_r4_mcp.utils.errors import FHIRValueSetError

# FHIR R4 Required Value Sets
# See: https://hl7.org/fhir/R4/terminologies-valuesets.html

VALUE_SETS: dict[str, list[str]] = {
    # Administrative Gender (required)
    # https://hl7.org/fhir/R4/valueset-administrative-gender.html
    "administrative-gender": ["male", "female", "other", "unknown"],
    # Observation Status (required)
    # https://hl7.org/fhir/R4/valueset-observation-status.html
    "observation-status": [
        "registered",
        "preliminary",
        "final",
        "amended",
        "corrected",
        "cancelled",
        "entered-in-error",
        "unknown",
    ],
    # Condition Clinical Status (required)
    # https://hl7.org/fhir/R4/valueset-condition-clinical.html
    "condition-clinical": [
        "active",
        "recurrence",
        "relapse",
        "inactive",
        "remission",
        "resolved",
    ],
    # Condition Verification Status (required)
    # https://hl7.org/fhir/R4/valueset-condition-ver-status.html
    "condition-ver-status": [
        "unconfirmed",
        "provisional",
        "differential",
        "confirmed",
        "refuted",
        "entered-in-error",
    ],
    # MedicationRequest Status (required)
    # https://hl7.org/fhir/R4/valueset-medicationrequest-status.html
    "medicationrequest-status": [
        "active",
        "on-hold",
        "cancelled",
        "completed",
        "entered-in-error",
        "stopped",
        "draft",
        "unknown",
    ],
    # MedicationRequest Intent (required)
    # https://hl7.org/fhir/R4/valueset-medicationrequest-intent.html
    "medicationrequest-intent": [
        "proposal",
        "plan",
        "order",
        "original-order",
        "reflex-order",
        "filler-order",
        "instance-order",
        "option",
    ],
    # Encounter Status (required)
    # https://hl7.org/fhir/R4/valueset-encounter-status.html
    "encounter-status": [
        "planned",
        "arrived",
        "triaged",
        "in-progress",
        "onleave",
        "finished",
        "cancelled",
        "entered-in-error",
        "unknown",
    ],
    # Encounter Class (extensible)
    # https://hl7.org/fhir/R4/v3/ActEncounterCode/vs.html
    "encounter-class": [
        "AMB",  # Ambulatory
        "EMER",  # Emergency
        "FLD",  # Field
        "HH",  # Home Health
        "IMP",  # Inpatient
        "ACUTE",  # Inpatient Acute
        "NONAC",  # Inpatient Non-Acute
        "OBSENC",  # Observation Encounter
        "PRENC",  # Pre-admission
        "SS",  # Short Stay
        "VR",  # Virtual
    ],
    # Allergy Intolerance Clinical Status (required)
    # https://hl7.org/fhir/R4/valueset-allergyintolerance-clinical.html
    "allergyintolerance-clinical": [
        "active",
        "inactive",
        "resolved",
    ],
    # Allergy Intolerance Verification Status (required)
    # https://hl7.org/fhir/R4/valueset-allergyintolerance-verification.html
    "allergyintolerance-verification": [
        "unconfirmed",
        "confirmed",
        "refuted",
        "entered-in-error",
    ],
    # Allergy Intolerance Type (required)
    # https://hl7.org/fhir/R4/valueset-allergy-intolerance-type.html
    "allergy-intolerance-type": [
        "allergy",
        "intolerance",
    ],
    # Allergy Intolerance Category (required)
    # https://hl7.org/fhir/R4/valueset-allergy-intolerance-category.html
    "allergy-intolerance-category": [
        "food",
        "medication",
        "environment",
        "biologic",
    ],
    # Allergy Intolerance Criticality (required)
    # https://hl7.org/fhir/R4/valueset-allergy-intolerance-criticality.html
    "allergy-intolerance-criticality": [
        "low",
        "high",
        "unable-to-assess",
    ],
    # CarePlan Status (required)
    # https://hl7.org/fhir/R4/valueset-request-status.html
    "careplan-status": [
        "draft",
        "active",
        "on-hold",
        "revoked",
        "completed",
        "entered-in-error",
        "unknown",
    ],
    # CarePlan Intent (required)
    # https://hl7.org/fhir/R4/valueset-care-plan-intent.html
    "careplan-intent": [
        "proposal",
        "plan",
        "order",
        "option",
    ],
    # Diagnostic Report Status (required)
    # https://hl7.org/fhir/R4/valueset-diagnostic-report-status.html
    "diagnostic-report-status": [
        "registered",
        "partial",
        "preliminary",
        "final",
        "amended",
        "corrected",
        "appended",
        "cancelled",
        "entered-in-error",
        "unknown",
    ],
    # Document Reference Status (required)
    # https://hl7.org/fhir/R4/valueset-document-reference-status.html
    "document-reference-status": [
        "current",
        "superseded",
        "entered-in-error",
    ],
    # Goal Status (required)
    # https://hl7.org/fhir/R4/valueset-goal-status.html
    "goal-status": [
        "proposed",
        "planned",
        "accepted",
        "active",
        "on-hold",
        "completed",
        "cancelled",
        "entered-in-error",
        "rejected",
    ],
    # Immunization Status (required)
    # https://hl7.org/fhir/R4/valueset-immunization-status.html
    "immunization-status": [
        "completed",
        "entered-in-error",
        "not-done",
    ],
    # Procedure Status (required)
    # https://hl7.org/fhir/R4/valueset-event-status.html
    "procedure-status": [
        "preparation",
        "in-progress",
        "not-done",
        "on-hold",
        "stopped",
        "completed",
        "entered-in-error",
        "unknown",
    ],
    # Service Request Status (required)
    # https://hl7.org/fhir/R4/valueset-request-status.html
    "servicerequest-status": [
        "draft",
        "active",
        "on-hold",
        "revoked",
        "completed",
        "entered-in-error",
        "unknown",
    ],
    # Service Request Intent (required)
    # https://hl7.org/fhir/R4/valueset-request-intent.html
    "servicerequest-intent": [
        "proposal",
        "plan",
        "directive",
        "order",
        "original-order",
        "reflex-order",
        "filler-order",
        "instance-order",
        "option",
    ],
    # Narrative Status (required)
    # https://hl7.org/fhir/R4/valueset-narrative-status.html
    "narrative-status": [
        "generated",
        "extensions",
        "additional",
        "empty",
    ],
}

# Mapping from resource type + field to value set name
FIELD_VALUE_SET_MAP: dict[str, dict[str, str]] = {
    "Patient": {
        "gender": "administrative-gender",
    },
    "Practitioner": {
        "gender": "administrative-gender",
    },
    "Observation": {
        "status": "observation-status",
    },
    "Condition": {
        "clinicalStatus.coding.code": "condition-clinical",
        "verificationStatus.coding.code": "condition-ver-status",
    },
    "MedicationRequest": {
        "status": "medicationrequest-status",
        "intent": "medicationrequest-intent",
    },
    "Encounter": {
        "status": "encounter-status",
        "class.code": "encounter-class",
    },
    "AllergyIntolerance": {
        "clinicalStatus.coding.code": "allergyintolerance-clinical",
        "verificationStatus.coding.code": "allergyintolerance-verification",
        "type": "allergy-intolerance-type",
        "category": "allergy-intolerance-category",
        "criticality": "allergy-intolerance-criticality",
    },
    "CarePlan": {
        "status": "careplan-status",
        "intent": "careplan-intent",
    },
    "DiagnosticReport": {
        "status": "diagnostic-report-status",
    },
    "DocumentReference": {
        "status": "document-reference-status",
    },
    "Goal": {
        "lifecycleStatus": "goal-status",
    },
    "Immunization": {
        "status": "immunization-status",
    },
    "Procedure": {
        "status": "procedure-status",
    },
    "ServiceRequest": {
        "status": "servicerequest-status",
        "intent": "servicerequest-intent",
    },
}


class ValueSetValidator:
    """Validator for FHIR value sets."""

    def __init__(self, value_sets: dict[str, list[str]] | None = None) -> None:
        """Initialize with custom or default value sets."""
        self._value_sets = value_sets or VALUE_SETS

    def validate_value(
        self,
        value_set_name: str,
        value: str,
        raise_error: bool = False,
    ) -> bool:
        """
        Validate a value against a named value set.

        Args:
            value_set_name: Name of the value set to validate against.
            value: The value to validate.
            raise_error: If True, raise FHIRValueSetError on invalid value.

        Returns:
            True if valid, False otherwise.

        Raises:
            FHIRValueSetError: If raise_error=True and value is invalid.
        """
        if value_set_name not in self._value_sets:
            # Unknown value set - allow the value (server will validate)
            return True

        allowed_values = self._value_sets[value_set_name]
        is_valid = value in allowed_values

        if not is_valid and raise_error:
            raise FHIRValueSetError(
                message=f"Value '{value}' is not valid for value set '{value_set_name}'",
                field=value_set_name,
                value=value,
                allowed_values=allowed_values,
            )

        return is_valid

    def get_allowed_values(self, value_set_name: str) -> list[str]:
        """Get the allowed values for a value set."""
        return self._value_sets.get(value_set_name, [])

    def validate_resource_field(
        self,
        resource_type: str,
        field_path: str,
        value: Any,
        raise_error: bool = False,
    ) -> bool:
        """
        Validate a resource field value against its associated value set.

        Args:
            resource_type: FHIR resource type (e.g., "Patient").
            field_path: Path to the field (e.g., "gender").
            value: The value to validate.
            raise_error: If True, raise FHIRValueSetError on invalid value.

        Returns:
            True if valid or no value set defined, False otherwise.
        """
        field_map = FIELD_VALUE_SET_MAP.get(resource_type, {})
        value_set_name = field_map.get(field_path)

        if not value_set_name:
            # No value set defined for this field
            return True

        return self.validate_value(value_set_name, value, raise_error)

    def get_value_set_for_field(
        self, resource_type: str, field_path: str
    ) -> str | None:
        """Get the value set name for a resource field."""
        return FIELD_VALUE_SET_MAP.get(resource_type, {}).get(field_path)


# Global validator instance
value_set_validator = ValueSetValidator()

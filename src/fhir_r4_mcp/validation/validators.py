"""FHIR R4 Resource Validators.

This module provides validation for FHIR R4 resources, checking required fields,
cardinality, and value set compliance.

See: https://hl7.org/fhir/R4/resource.html
"""

from dataclasses import dataclass, field
from typing import Any

from fhir_r4_mcp.utils.errors import (
    FHIRRequiredFieldError,
    FHIRValidationError,
    FHIRValueSetError,
)
from fhir_r4_mcp.validation.coding_systems import coding_system_validator
from fhir_r4_mcp.validation.value_sets import value_set_validator


@dataclass
class ValidationResult:
    """Result of validating a FHIR resource."""

    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add_error(self, message: str) -> None:
        """Add an error message."""
        self.errors.append(message)
        self.valid = False

    def add_warning(self, message: str) -> None:
        """Add a warning message."""
        self.warnings.append(message)


# Required fields by resource type
# Format: {resource_type: [(field_path, error_message, is_choice_type), ...]}
# For choice types (e.g., medication[x]), any of the variants satisfies the requirement
REQUIRED_FIELDS: dict[str, list[tuple[str, str, bool]]] = {
    "Patient": [
        # Patient has no strictly required fields per spec, but identifier or name is recommended
    ],
    "Observation": [
        ("status", "Observation.status is required", False),
        ("code", "Observation.code is required", False),
    ],
    "Condition": [
        ("subject", "Condition.subject is required", False),
    ],
    "MedicationRequest": [
        ("status", "MedicationRequest.status is required", False),
        ("intent", "MedicationRequest.intent is required", False),
        ("medication", "MedicationRequest.medication[x] is required", True),
        ("subject", "MedicationRequest.subject is required", False),
    ],
    "Encounter": [
        ("status", "Encounter.status is required", False),
        ("class", "Encounter.class is required", False),
    ],
    "AllergyIntolerance": [
        ("patient", "AllergyIntolerance.patient is required", False),
    ],
    "CarePlan": [
        ("status", "CarePlan.status is required", False),
        ("intent", "CarePlan.intent is required", False),
        ("subject", "CarePlan.subject is required", False),
    ],
    "DiagnosticReport": [
        ("status", "DiagnosticReport.status is required", False),
        ("code", "DiagnosticReport.code is required", False),
    ],
    "DocumentReference": [
        ("status", "DocumentReference.status is required", False),
        ("content", "DocumentReference.content is required", False),
    ],
    "Goal": [
        ("lifecycleStatus", "Goal.lifecycleStatus is required", False),
        ("description", "Goal.description is required", False),
        ("subject", "Goal.subject is required", False),
    ],
    "Immunization": [
        ("status", "Immunization.status is required", False),
        ("vaccineCode", "Immunization.vaccineCode is required", False),
        ("patient", "Immunization.patient is required", False),
        ("occurrence", "Immunization.occurrence[x] is required", True),
    ],
    "Procedure": [
        ("status", "Procedure.status is required", False),
        ("subject", "Procedure.subject is required", False),
    ],
    "ServiceRequest": [
        ("status", "ServiceRequest.status is required", False),
        ("intent", "ServiceRequest.intent is required", False),
        ("subject", "ServiceRequest.subject is required", False),
    ],
    "Group": [
        ("type", "Group.type is required", False),
        ("actual", "Group.actual is required", False),
    ],
}

# Choice type field variants
# Maps base field name to all possible variants
CHOICE_TYPE_VARIANTS: dict[str, list[str]] = {
    "medication": [
        "medicationCodeableConcept",
        "medicationReference",
    ],
    "occurrence": [
        "occurrenceDateTime",
        "occurrenceString",
    ],
    "value": [
        "valueQuantity",
        "valueCodeableConcept",
        "valueString",
        "valueBoolean",
        "valueInteger",
        "valueRange",
        "valueRatio",
        "valueSampledData",
        "valueTime",
        "valueDateTime",
        "valuePeriod",
    ],
    "effective": [
        "effectiveDateTime",
        "effectivePeriod",
        "effectiveTiming",
        "effectiveInstant",
    ],
    "onset": [
        "onsetDateTime",
        "onsetAge",
        "onsetPeriod",
        "onsetRange",
        "onsetString",
    ],
    "abatement": [
        "abatementDateTime",
        "abatementAge",
        "abatementPeriod",
        "abatementRange",
        "abatementString",
    ],
}


class FHIRValidator:
    """Validator for FHIR R4 resources."""

    def __init__(self) -> None:
        """Initialize the validator."""
        self._required_fields = REQUIRED_FIELDS
        self._choice_variants = CHOICE_TYPE_VARIANTS

    def validate(
        self,
        resource: dict[str, Any],
        raise_on_error: bool = False,
    ) -> ValidationResult:
        """
        Validate a FHIR resource.

        Args:
            resource: The FHIR resource to validate.
            raise_on_error: If True, raise an exception on first error.

        Returns:
            ValidationResult with errors and warnings.

        Raises:
            FHIRValidationError: If raise_on_error=True and validation fails.
        """
        result = ValidationResult(valid=True)

        # Check resourceType
        resource_type = resource.get("resourceType")
        if not resource_type:
            result.add_error("resourceType is required")
            if raise_on_error:
                raise FHIRValidationError(
                    message="resourceType is required",
                    field="resourceType",
                )
            return result

        # Validate required fields
        self._validate_required_fields(resource, resource_type, result, raise_on_error)

        # Validate value sets
        self._validate_value_sets(resource, resource_type, result, raise_on_error)

        # Validate coding elements
        self._validate_codings(resource, result)

        return result

    def _validate_required_fields(
        self,
        resource: dict[str, Any],
        resource_type: str,
        result: ValidationResult,
        raise_on_error: bool,
    ) -> None:
        """Validate required fields for a resource."""
        required = self._required_fields.get(resource_type, [])

        for field_name, error_message, is_choice in required:
            if is_choice:
                # Check if any choice variant is present
                variants = self._choice_variants.get(field_name, [field_name])
                has_value = any(
                    self._get_field_value(resource, variant) is not None
                    for variant in variants
                )
            else:
                has_value = self._get_field_value(resource, field_name) is not None

            if not has_value:
                result.add_error(error_message)
                if raise_on_error:
                    raise FHIRRequiredFieldError(
                        message=error_message,
                        field=field_name,
                        resource_type=resource_type,
                    )

    def _validate_value_sets(
        self,
        resource: dict[str, Any],
        resource_type: str,
        result: ValidationResult,
        raise_on_error: bool,
    ) -> None:
        """Validate fields against their value sets."""
        # Common status fields
        status_fields = {
            "Observation": ("status", "observation-status"),
            "Condition": None,  # Handled separately (clinicalStatus)
            "MedicationRequest": ("status", "medicationrequest-status"),
            "Encounter": ("status", "encounter-status"),
            "DiagnosticReport": ("status", "diagnostic-report-status"),
            "DocumentReference": ("status", "document-reference-status"),
            "Goal": ("lifecycleStatus", "goal-status"),
            "Immunization": ("status", "immunization-status"),
            "Procedure": ("status", "procedure-status"),
            "ServiceRequest": ("status", "servicerequest-status"),
            "CarePlan": ("status", "careplan-status"),
        }

        # Validate status field if applicable
        status_info = status_fields.get(resource_type)
        if status_info:
            field_name, value_set_name = status_info
            value = resource.get(field_name)
            if value:
                try:
                    value_set_validator.validate_value(
                        value_set_name, value, raise_error=True
                    )
                except FHIRValueSetError as e:
                    result.add_error(e.message)
                    if raise_on_error:
                        raise

        # Validate intent for resources that have it
        intent_fields = {
            "MedicationRequest": "medicationrequest-intent",
            "ServiceRequest": "servicerequest-intent",
            "CarePlan": "careplan-intent",
        }
        if resource_type in intent_fields:
            intent = resource.get("intent")
            if intent:
                value_set_name = intent_fields[resource_type]
                try:
                    value_set_validator.validate_value(
                        value_set_name, intent, raise_error=True
                    )
                except FHIRValueSetError as e:
                    result.add_error(e.message)
                    if raise_on_error:
                        raise

        # Validate gender for Patient/Practitioner
        if resource_type in ("Patient", "Practitioner"):
            gender = resource.get("gender")
            if gender:
                try:
                    value_set_validator.validate_value(
                        "administrative-gender", gender, raise_error=True
                    )
                except FHIRValueSetError as e:
                    result.add_error(e.message)
                    if raise_on_error:
                        raise

        # Validate Condition clinical status
        if resource_type == "Condition":
            clinical_status = resource.get("clinicalStatus", {})
            codings = clinical_status.get("coding", [])
            for coding in codings:
                code = coding.get("code")
                if code:
                    try:
                        value_set_validator.validate_value(
                            "condition-clinical", code, raise_error=True
                        )
                    except FHIRValueSetError as e:
                        result.add_error(f"Condition.clinicalStatus: {e.message}")
                        if raise_on_error:
                            raise

    def _validate_codings(
        self,
        resource: dict[str, Any],
        result: ValidationResult,
    ) -> None:
        """Validate coding elements in the resource."""
        # Find and validate CodeableConcept and Coding elements
        self._validate_coding_recursive(resource, "", result)

    def _validate_coding_recursive(
        self,
        obj: Any,
        path: str,
        result: ValidationResult,
    ) -> None:
        """Recursively validate coding elements."""
        if isinstance(obj, dict):
            # Check if this is a CodeableConcept
            if "coding" in obj and isinstance(obj["coding"], list):
                errors = coding_system_validator.validate_codeable_concept(
                    obj, require_coding=False
                )
                for error in errors:
                    result.add_warning(f"{path}: {error}")

            # Check if this is a Coding
            if "system" in obj and "code" in obj and "coding" not in obj:
                errors = coding_system_validator.validate_coding(obj)
                for error in errors:
                    result.add_warning(f"{path}: {error}")

            # Recurse into children
            for key, value in obj.items():
                child_path = f"{path}.{key}" if path else key
                self._validate_coding_recursive(value, child_path, result)

        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                child_path = f"{path}[{i}]"
                self._validate_coding_recursive(item, child_path, result)

    def _get_field_value(self, resource: dict[str, Any], field_path: str) -> Any:
        """Get a field value from a resource by path."""
        parts = field_path.split(".")
        current = resource
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
            if current is None:
                return None
        return current

    def validate_reference(
        self,
        reference: dict[str, Any],
        allowed_types: list[str] | None = None,
    ) -> list[str]:
        """
        Validate a FHIR Reference element.

        Args:
            reference: FHIR Reference element dict.
            allowed_types: List of allowed resource types for the reference.

        Returns:
            List of validation error messages.
        """
        errors = []

        ref_value = reference.get("reference")
        ref_type = reference.get("type")

        # Must have reference, identifier, or display
        if not ref_value and not reference.get("identifier") and not reference.get("display"):
            errors.append("Reference must have reference, identifier, or display")

        # Validate reference format if present
        if ref_value:
            # Should be ResourceType/id or absolute URL
            if "/" in ref_value and not ref_value.startswith("http"):
                parts = ref_value.split("/")
                if len(parts) >= 2:
                    resource_type = parts[-2]
                    if allowed_types and resource_type not in allowed_types:
                        errors.append(
                            f"Reference type '{resource_type}' not in allowed types: {allowed_types}"
                        )

        # Validate type if present
        if ref_type and allowed_types and ref_type not in allowed_types:
            errors.append(
                f"Reference type '{ref_type}' not in allowed types: {allowed_types}"
            )

        return errors


# Global validator instance
fhir_validator = FHIRValidator()

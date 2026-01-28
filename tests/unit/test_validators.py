"""Unit tests for FHIR validators."""

import pytest

from fhir_r4_mcp.utils.errors import (
    FHIRRequiredFieldError,
    FHIRValidationError,
    FHIRValueSetError,
)
from fhir_r4_mcp.validation import (
    FHIRValidator,
    ValidationResult,
    fhir_validator,
)


class TestFHIRValidator:
    """Tests for FHIRValidator class."""

    def test_validate_observation_valid(self):
        """Test validating a valid Observation resource."""
        observation = {
            "resourceType": "Observation",
            "status": "final",
            "code": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "8867-4",
                        "display": "Heart rate",
                    }
                ]
            },
            "subject": {"reference": "Patient/123"},
            "valueQuantity": {"value": 72, "unit": "/min"},
        }

        result = fhir_validator.validate(observation)

        assert result.valid is True
        assert len(result.errors) == 0

    def test_validate_observation_missing_status(self):
        """Test validating Observation without required status."""
        observation = {
            "resourceType": "Observation",
            "code": {
                "coding": [
                    {"system": "http://loinc.org", "code": "8867-4"}
                ]
            },
        }

        result = fhir_validator.validate(observation)

        assert result.valid is False
        assert any("status" in error.lower() for error in result.errors)

    def test_validate_observation_missing_code(self):
        """Test validating Observation without required code."""
        observation = {
            "resourceType": "Observation",
            "status": "final",
        }

        result = fhir_validator.validate(observation)

        assert result.valid is False
        assert any("code" in error.lower() for error in result.errors)

    def test_validate_observation_invalid_status(self):
        """Test validating Observation with invalid status value."""
        observation = {
            "resourceType": "Observation",
            "status": "invalid-status",
            "code": {
                "coding": [
                    {"system": "http://loinc.org", "code": "8867-4"}
                ]
            },
        }

        result = fhir_validator.validate(observation)

        assert result.valid is False
        assert any("status" in error.lower() or "value" in error.lower() for error in result.errors)

    def test_validate_patient_valid(self):
        """Test validating a valid Patient resource."""
        patient = {
            "resourceType": "Patient",
            "name": [{"family": "Smith", "given": ["John"]}],
            "gender": "male",
            "birthDate": "1990-01-01",
        }

        result = fhir_validator.validate(patient)

        assert result.valid is True

    def test_validate_patient_invalid_gender(self):
        """Test validating Patient with invalid gender."""
        patient = {
            "resourceType": "Patient",
            "name": [{"family": "Smith"}],
            "gender": "invalid",
        }

        result = fhir_validator.validate(patient)

        assert result.valid is False
        assert any("gender" in error.lower() for error in result.errors)

    def test_validate_medication_request_valid(self):
        """Test validating a valid MedicationRequest."""
        med_request = {
            "resourceType": "MedicationRequest",
            "status": "active",
            "intent": "order",
            "medicationCodeableConcept": {
                "coding": [
                    {
                        "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                        "code": "197361",
                        "display": "Acetaminophen 325 MG Oral Tablet",
                    }
                ]
            },
            "subject": {"reference": "Patient/123"},
        }

        result = fhir_validator.validate(med_request)

        assert result.valid is True

    def test_validate_medication_request_missing_required(self):
        """Test validating MedicationRequest without required fields."""
        med_request = {
            "resourceType": "MedicationRequest",
            "status": "active",
            # Missing: intent, medication[x], subject
        }

        result = fhir_validator.validate(med_request)

        assert result.valid is False
        assert len(result.errors) >= 2  # At least intent and medication[x]

    def test_validate_medication_request_invalid_intent(self):
        """Test validating MedicationRequest with invalid intent."""
        med_request = {
            "resourceType": "MedicationRequest",
            "status": "active",
            "intent": "bad-intent",
            "medicationCodeableConcept": {
                "coding": [{"system": "http://rxnorm", "code": "123"}]
            },
            "subject": {"reference": "Patient/123"},
        }

        result = fhir_validator.validate(med_request)

        assert result.valid is False

    def test_validate_encounter_valid(self):
        """Test validating a valid Encounter."""
        encounter = {
            "resourceType": "Encounter",
            "status": "in-progress",
            "class": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "AMB",
                "display": "Ambulatory",
            },
            "subject": {"reference": "Patient/123"},
        }

        result = fhir_validator.validate(encounter)

        assert result.valid is True

    def test_validate_encounter_invalid_status(self):
        """Test validating Encounter with invalid status."""
        encounter = {
            "resourceType": "Encounter",
            "status": "bad-status",
            "class": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "AMB",
            },
        }

        result = fhir_validator.validate(encounter)

        assert result.valid is False

    def test_validate_condition_valid(self):
        """Test validating a valid Condition."""
        condition = {
            "resourceType": "Condition",
            "clinicalStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                        "code": "active",
                    }
                ]
            },
            "subject": {"reference": "Patient/123"},
            "code": {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "44054006",
                        "display": "Type 2 diabetes mellitus",
                    }
                ]
            },
        }

        result = fhir_validator.validate(condition)

        assert result.valid is True

    def test_validate_condition_invalid_clinical_status(self):
        """Test validating Condition with invalid clinical status."""
        condition = {
            "resourceType": "Condition",
            "clinicalStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                        "code": "bad-status",
                    }
                ]
            },
            "subject": {"reference": "Patient/123"},
        }

        result = fhir_validator.validate(condition)

        assert result.valid is False

    def test_validate_missing_resource_type(self):
        """Test validating resource without resourceType."""
        resource = {
            "name": [{"family": "Smith"}],
        }

        result = fhir_validator.validate(resource)

        assert result.valid is False
        assert any("resourceType" in error for error in result.errors)

    def test_validate_raises_on_error(self):
        """Test that raise_on_error=True raises exception."""
        resource = {
            "name": [{"family": "Smith"}],
        }

        with pytest.raises(FHIRValidationError):
            fhir_validator.validate(resource, raise_on_error=True)

    def test_validate_group_valid(self):
        """Test validating a valid Group resource."""
        group = {
            "resourceType": "Group",
            "type": "person",
            "actual": True,
            "member": [
                {"entity": {"reference": "Patient/123"}},
            ],
        }

        result = fhir_validator.validate(group)

        assert result.valid is True

    def test_validate_group_missing_type(self):
        """Test validating Group without required type."""
        group = {
            "resourceType": "Group",
            "actual": True,
        }

        result = fhir_validator.validate(group)

        assert result.valid is False


class TestValidationResult:
    """Tests for ValidationResult class."""

    def test_add_error(self):
        """Test adding an error to result."""
        result = ValidationResult(valid=True)
        result.add_error("Test error")

        assert result.valid is False
        assert "Test error" in result.errors

    def test_add_warning(self):
        """Test adding a warning to result."""
        result = ValidationResult(valid=True)
        result.add_warning("Test warning")

        assert result.valid is True  # Warnings don't invalidate
        assert "Test warning" in result.warnings


class TestReferenceValidation:
    """Tests for FHIR Reference validation."""

    def test_validate_reference_valid(self):
        """Test validating a valid reference."""
        reference = {
            "reference": "Patient/123",
        }

        errors = fhir_validator.validate_reference(reference)

        assert len(errors) == 0

    def test_validate_reference_with_type(self):
        """Test validating reference with type constraint."""
        reference = {
            "reference": "Patient/123",
            "type": "Patient",
        }

        errors = fhir_validator.validate_reference(reference, allowed_types=["Patient"])

        assert len(errors) == 0

    def test_validate_reference_wrong_type(self):
        """Test validating reference with wrong type."""
        reference = {
            "reference": "Observation/123",
        }

        errors = fhir_validator.validate_reference(
            reference, allowed_types=["Patient"]
        )

        assert len(errors) > 0

    def test_validate_reference_missing_all(self):
        """Test validating reference missing all fields."""
        reference = {}

        errors = fhir_validator.validate_reference(reference)

        assert len(errors) > 0

    def test_validate_reference_with_display_only(self):
        """Test validating reference with only display."""
        reference = {
            "display": "John Smith",
        }

        errors = fhir_validator.validate_reference(reference)

        assert len(errors) == 0  # display alone is valid

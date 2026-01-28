"""Unit tests for FHIR value set validation."""

import pytest

from fhir_r4_mcp.utils.errors import FHIRValueSetError
from fhir_r4_mcp.validation import (
    VALUE_SETS,
    ValueSetValidator,
    value_set_validator,
)


class TestValueSets:
    """Tests for VALUE_SETS definitions."""

    def test_observation_status_values(self):
        """Test observation status value set contains expected values."""
        statuses = VALUE_SETS["observation-status"]

        assert "final" in statuses
        assert "preliminary" in statuses
        assert "cancelled" in statuses
        assert "entered-in-error" in statuses

    def test_condition_clinical_values(self):
        """Test condition clinical status value set."""
        statuses = VALUE_SETS["condition-clinical"]

        assert "active" in statuses
        assert "resolved" in statuses
        assert "inactive" in statuses

    def test_administrative_gender_values(self):
        """Test administrative gender value set."""
        genders = VALUE_SETS["administrative-gender"]

        assert "male" in genders
        assert "female" in genders
        assert "other" in genders
        assert "unknown" in genders
        assert len(genders) == 4

    def test_medication_request_status_values(self):
        """Test medication request status value set."""
        statuses = VALUE_SETS["medicationrequest-status"]

        assert "active" in statuses
        assert "completed" in statuses
        assert "cancelled" in statuses
        assert "stopped" in statuses

    def test_medication_request_intent_values(self):
        """Test medication request intent value set."""
        intents = VALUE_SETS["medicationrequest-intent"]

        assert "order" in intents
        assert "proposal" in intents
        assert "plan" in intents

    def test_encounter_status_values(self):
        """Test encounter status value set."""
        statuses = VALUE_SETS["encounter-status"]

        assert "in-progress" in statuses
        assert "finished" in statuses
        assert "cancelled" in statuses

    def test_encounter_class_values(self):
        """Test encounter class value set."""
        classes = VALUE_SETS["encounter-class"]

        assert "AMB" in classes  # Ambulatory
        assert "IMP" in classes  # Inpatient
        assert "EMER" in classes  # Emergency


class TestValueSetValidator:
    """Tests for ValueSetValidator class."""

    def test_validate_valid_observation_status(self):
        """Test validating a valid observation status."""
        assert value_set_validator.validate_value("observation-status", "final") is True

    def test_validate_invalid_observation_status(self):
        """Test validating an invalid observation status."""
        assert value_set_validator.validate_value("observation-status", "bad-status") is False

    def test_validate_raises_on_invalid(self):
        """Test that raise_error=True raises exception for invalid value."""
        with pytest.raises(FHIRValueSetError) as exc_info:
            value_set_validator.validate_value(
                "observation-status",
                "bad-status",
                raise_error=True,
            )

        error = exc_info.value
        assert "bad-status" in error.message
        assert "observation-status" in error.message

    def test_validate_unknown_value_set(self):
        """Test that unknown value set returns True (allows value)."""
        assert value_set_validator.validate_value("unknown-set", "any-value") is True

    def test_get_allowed_values(self):
        """Test getting allowed values for a value set."""
        values = value_set_validator.get_allowed_values("administrative-gender")

        assert "male" in values
        assert "female" in values
        assert len(values) == 4

    def test_get_allowed_values_unknown_set(self):
        """Test getting allowed values for unknown set returns empty list."""
        values = value_set_validator.get_allowed_values("unknown-set")

        assert values == []

    def test_validate_resource_field_patient_gender(self):
        """Test validating Patient.gender field."""
        assert value_set_validator.validate_resource_field(
            "Patient", "gender", "male"
        ) is True

        assert value_set_validator.validate_resource_field(
            "Patient", "gender", "invalid"
        ) is False

    def test_validate_resource_field_observation_status(self):
        """Test validating Observation.status field."""
        assert value_set_validator.validate_resource_field(
            "Observation", "status", "final"
        ) is True

        assert value_set_validator.validate_resource_field(
            "Observation", "status", "bad"
        ) is False

    def test_validate_resource_field_no_mapping(self):
        """Test validating field with no value set mapping returns True."""
        # Patient.name has no value set
        assert value_set_validator.validate_resource_field(
            "Patient", "name", "anything"
        ) is True

    def test_validate_medication_request_intent(self):
        """Test validating MedicationRequest.intent field."""
        assert value_set_validator.validate_resource_field(
            "MedicationRequest", "intent", "order"
        ) is True

        assert value_set_validator.validate_resource_field(
            "MedicationRequest", "intent", "bad-intent"
        ) is False

    def test_validate_encounter_status(self):
        """Test validating Encounter.status field."""
        assert value_set_validator.validate_resource_field(
            "Encounter", "status", "in-progress"
        ) is True

        assert value_set_validator.validate_resource_field(
            "Encounter", "status", "bad-status"
        ) is False

    def test_get_value_set_for_field(self):
        """Test getting value set name for a field."""
        value_set = value_set_validator.get_value_set_for_field("Patient", "gender")
        assert value_set == "administrative-gender"

        value_set = value_set_validator.get_value_set_for_field("Observation", "status")
        assert value_set == "observation-status"

        value_set = value_set_validator.get_value_set_for_field("Patient", "name")
        assert value_set is None

    def test_custom_value_sets(self):
        """Test using custom value sets."""
        custom_sets = {
            "custom-status": ["a", "b", "c"],
        }
        validator = ValueSetValidator(value_sets=custom_sets)

        assert validator.validate_value("custom-status", "a") is True
        assert validator.validate_value("custom-status", "d") is False


class TestAllValueSets:
    """Tests to ensure all value sets are properly defined."""

    @pytest.mark.parametrize("value_set_name", list(VALUE_SETS.keys()))
    def test_value_set_not_empty(self, value_set_name):
        """Test that all value sets have at least one value."""
        values = VALUE_SETS[value_set_name]
        assert len(values) > 0

    @pytest.mark.parametrize("value_set_name", list(VALUE_SETS.keys()))
    def test_value_set_no_duplicates(self, value_set_name):
        """Test that value sets have no duplicate values."""
        values = VALUE_SETS[value_set_name]
        assert len(values) == len(set(values))

    def test_all_required_value_sets_present(self):
        """Test that all required value sets are defined."""
        required_sets = [
            "observation-status",
            "condition-clinical",
            "administrative-gender",
            "medicationrequest-status",
            "medicationrequest-intent",
            "encounter-status",
        ]

        for vs_name in required_sets:
            assert vs_name in VALUE_SETS, f"Missing required value set: {vs_name}"

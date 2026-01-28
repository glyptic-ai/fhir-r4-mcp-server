"""Unit tests for chained search parameter support."""

import pytest

from fhir_r4_mcp.validation.search_params import (
    ChainedParam,
    ChainedSearchParser,
    chained_search_parser,
)


class TestChainedParam:
    """Tests for ChainedParam dataclass."""

    def test_chained_param_creation(self):
        """Test creating a chained param."""
        param = ChainedParam(
            base_param="subject",
            target_type="Patient",
            chained_param="name",
            full_chain="subject:Patient.name",
        )

        assert param.base_param == "subject"
        assert param.target_type == "Patient"
        assert param.chained_param == "name"

    def test_chained_param_without_type(self):
        """Test chained param without explicit type."""
        param = ChainedParam(
            base_param="patient",
            target_type=None,
            chained_param="birthdate",
            full_chain="patient.birthdate",
        )

        assert param.base_param == "patient"
        assert param.target_type is None


class TestChainedSearchParser:
    """Tests for ChainedSearchParser class."""

    @pytest.fixture
    def parser(self):
        """Create a test parser."""
        return ChainedSearchParser()

    def test_parse_explicit_type(self, parser):
        """Test parsing chain with explicit type."""
        result = parser.parse("subject:Patient.name")

        assert result is not None
        assert result.base_param == "subject"
        assert result.target_type == "Patient"
        assert result.chained_param == "name"

    def test_parse_simple_chain(self, parser):
        """Test parsing simple chain without type."""
        result = parser.parse("patient.birthdate")

        assert result is not None
        assert result.base_param == "patient"
        assert result.target_type is None
        assert result.chained_param == "birthdate"

    def test_parse_non_chained(self, parser):
        """Test parsing non-chained parameter returns None."""
        result = parser.parse("status")

        assert result is None

    def test_parse_modifier_only(self, parser):
        """Test parsing parameter with modifier but no chain."""
        result = parser.parse("name:exact")

        assert result is None

    def test_validate_chain_valid(self, parser):
        """Test validating a valid chain."""
        chain = ChainedParam(
            base_param="subject",
            target_type="Patient",
            chained_param="name",
            full_chain="subject:Patient.name",
        )

        errors = parser.validate_chain("Observation", chain)

        assert len(errors) == 0

    def test_validate_chain_invalid_base_param(self, parser):
        """Test validating chain with invalid base parameter."""
        chain = ChainedParam(
            base_param="invalid_param",
            target_type="Patient",
            chained_param="name",
            full_chain="invalid_param:Patient.name",
        )

        errors = parser.validate_chain("Observation", chain)

        assert len(errors) > 0
        assert "invalid_param" in errors[0].lower()

    def test_validate_chain_invalid_target_type(self, parser):
        """Test validating chain with invalid target type."""
        chain = ChainedParam(
            base_param="subject",
            target_type="InvalidType",
            chained_param="name",
            full_chain="subject:InvalidType.name",
        )

        errors = parser.validate_chain("Observation", chain)

        assert len(errors) > 0

    def test_validate_chain_raise_on_error(self, parser):
        """Test that validate_chain raises on error when requested."""
        chain = ChainedParam(
            base_param="invalid",
            target_type="Patient",
            chained_param="name",
            full_chain="invalid:Patient.name",
        )

        with pytest.raises(Exception):
            parser.validate_chain("Observation", chain, raise_on_error=True)

    def test_get_target_types(self, parser):
        """Test getting target types for a reference parameter."""
        targets = parser.get_target_types("Observation", "subject")

        assert "Patient" in targets
        assert "Group" in targets

    def test_get_target_types_unknown_resource(self, parser):
        """Test getting target types for unknown resource."""
        targets = parser.get_target_types("UnknownResource", "subject")

        assert targets == []


class TestGlobalChainedSearchParser:
    """Tests for the global chained_search_parser instance."""

    def test_global_instance_exists(self):
        """Test that global instance is available."""
        assert chained_search_parser is not None
        assert isinstance(chained_search_parser, ChainedSearchParser)

    def test_global_instance_parse(self):
        """Test parsing with global instance."""
        result = chained_search_parser.parse("subject:Patient.identifier")

        assert result is not None
        assert result.target_type == "Patient"
        assert result.chained_param == "identifier"


class TestChainedSearchUseCases:
    """Tests for common chained search use cases."""

    @pytest.fixture
    def parser(self):
        """Create a test parser."""
        return ChainedSearchParser()

    def test_observation_patient_name(self, parser):
        """Test Observation?subject:Patient.name=smith pattern."""
        chain = parser.parse("subject:Patient.name")

        assert chain is not None
        errors = parser.validate_chain("Observation", chain)
        assert len(errors) == 0

    def test_medication_request_patient_birthdate(self, parser):
        """Test MedicationRequest?subject:Patient.birthdate pattern."""
        chain = parser.parse("subject:Patient.birthdate")

        assert chain is not None
        errors = parser.validate_chain("MedicationRequest", chain)
        assert len(errors) == 0

    def test_condition_patient_identifier(self, parser):
        """Test Condition?subject:Patient.identifier pattern."""
        chain = parser.parse("subject:Patient.identifier")

        assert chain is not None
        errors = parser.validate_chain("Condition", chain)
        assert len(errors) == 0

    def test_encounter_patient_family(self, parser):
        """Test Encounter?patient:Patient.family pattern."""
        chain = parser.parse("patient.family")

        assert chain is not None
        assert chain.base_param == "patient"

    def test_diagnostic_report_encounter(self, parser):
        """Test DiagnosticReport?encounter.patient pattern."""
        # This is a reverse chain - encounter -> patient
        chain = parser.parse("encounter.patient")

        assert chain is not None
        assert chain.base_param == "encounter"
        assert chain.chained_param == "patient"

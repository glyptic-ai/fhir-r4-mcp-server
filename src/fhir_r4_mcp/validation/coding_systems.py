"""FHIR R4 Coding System definitions and validation.

This module contains the standard coding systems used in FHIR R4 resources
and provides utilities for working with coded values.

See: https://hl7.org/fhir/R4/terminologies-systems.html
"""

from dataclasses import dataclass
from typing import Any

# Standard FHIR Coding Systems
# See: https://hl7.org/fhir/R4/terminologies-systems.html

CODING_SYSTEMS: dict[str, dict[str, str]] = {
    # Medical Terminology Systems
    "http://loinc.org": {
        "name": "LOINC",
        "title": "Logical Observation Identifiers Names and Codes",
        "description": "Laboratory and clinical observations",
        "oid": "2.16.840.1.113883.6.1",
    },
    "http://snomed.info/sct": {
        "name": "SNOMED-CT",
        "title": "Systematized Nomenclature of Medicine - Clinical Terms",
        "description": "Clinical terminology for diagnoses, procedures, findings",
        "oid": "2.16.840.1.113883.6.96",
    },
    "http://www.nlm.nih.gov/research/umls/rxnorm": {
        "name": "RxNorm",
        "title": "RxNorm",
        "description": "Normalized drug names and codes",
        "oid": "2.16.840.1.113883.6.88",
    },
    "http://hl7.org/fhir/sid/icd-10-cm": {
        "name": "ICD-10-CM",
        "title": "International Classification of Diseases, 10th Revision, Clinical Modification",
        "description": "Diagnosis codes for US healthcare",
        "oid": "2.16.840.1.113883.6.90",
    },
    "http://hl7.org/fhir/sid/icd-10": {
        "name": "ICD-10",
        "title": "International Classification of Diseases, 10th Revision",
        "description": "International diagnosis classification",
        "oid": "2.16.840.1.113883.6.3",
    },
    "http://www.ama-assn.org/go/cpt": {
        "name": "CPT",
        "title": "Current Procedural Terminology",
        "description": "Procedure codes",
        "oid": "2.16.840.1.113883.6.12",
    },
    "http://hl7.org/fhir/sid/ndc": {
        "name": "NDC",
        "title": "National Drug Code",
        "description": "US drug identification numbers",
        "oid": "2.16.840.1.113883.6.69",
    },
    "http://unitsofmeasure.org": {
        "name": "UCUM",
        "title": "Unified Code for Units of Measure",
        "description": "Scientific units of measure",
        "oid": "2.16.840.1.113883.6.8",
    },
    # FHIR-specific Code Systems
    "http://terminology.hl7.org/CodeSystem/observation-category": {
        "name": "ObservationCategory",
        "title": "Observation Category Codes",
        "description": "Category codes for observations",
    },
    "http://terminology.hl7.org/CodeSystem/condition-category": {
        "name": "ConditionCategory",
        "title": "Condition Category Codes",
        "description": "Category codes for conditions",
    },
    "http://terminology.hl7.org/CodeSystem/condition-clinical": {
        "name": "ConditionClinicalStatus",
        "title": "Condition Clinical Status Codes",
        "description": "Clinical status codes for conditions",
    },
    "http://terminology.hl7.org/CodeSystem/condition-ver-status": {
        "name": "ConditionVerificationStatus",
        "title": "Condition Verification Status Codes",
        "description": "Verification status codes for conditions",
    },
    "http://terminology.hl7.org/CodeSystem/v3-ActCode": {
        "name": "ActCode",
        "title": "HL7 V3 Act Code",
        "description": "Act codes including encounter class",
    },
}

# Common LOINC codes for clinical notes (used in DocumentReference)
LOINC_NOTE_TYPES: dict[str, dict[str, str]] = {
    "11506-3": {"display": "Progress note", "category": "progress"},
    "18842-5": {"display": "Discharge summary", "category": "discharge"},
    "34117-2": {"display": "History and physical note", "category": "history"},
    "11488-4": {"display": "Consultation note", "category": "consult"},
    "28570-0": {"display": "Procedure note", "category": "procedure"},
    "11504-8": {"display": "Surgical operation note", "category": "surgical"},
    "34133-9": {"display": "Summary of episode note", "category": "episode"},
    "47039-3": {"display": "Hospital admission history and physical note", "category": "admission"},
    "57133-1": {"display": "Referral note", "category": "referral"},
}

# Common LOINC codes for vital signs
LOINC_VITAL_SIGNS: dict[str, dict[str, str]] = {
    "8867-4": {"display": "Heart rate", "unit": "/min"},
    "9279-1": {"display": "Respiratory rate", "unit": "/min"},
    "8310-5": {"display": "Body temperature", "unit": "Cel"},
    "85354-9": {"display": "Blood pressure panel", "unit": None},
    "8480-6": {"display": "Systolic blood pressure", "unit": "mm[Hg]"},
    "8462-4": {"display": "Diastolic blood pressure", "unit": "mm[Hg]"},
    "2708-6": {"display": "Oxygen saturation", "unit": "%"},
    "29463-7": {"display": "Body weight", "unit": "kg"},
    "8302-2": {"display": "Body height", "unit": "cm"},
    "39156-5": {"display": "Body mass index", "unit": "kg/m2"},
}

# Common Observation category codes
OBSERVATION_CATEGORY_CODES: dict[str, str] = {
    "vital-signs": "Vital Signs",
    "laboratory": "Laboratory",
    "imaging": "Imaging",
    "procedure": "Procedure",
    "survey": "Survey",
    "exam": "Exam",
    "therapy": "Therapy",
    "activity": "Activity",
    "social-history": "Social History",
}

# Common Condition category codes
CONDITION_CATEGORY_CODES: dict[str, str] = {
    "problem-list-item": "Problem List Item",
    "encounter-diagnosis": "Encounter Diagnosis",
    "health-concern": "Health Concern",
}


@dataclass
class CodingInfo:
    """Information about a coding."""

    system: str
    code: str
    display: str | None = None
    version: str | None = None


class CodingSystemValidator:
    """Validator and utilities for FHIR coding systems."""

    def __init__(self, coding_systems: dict[str, dict[str, str]] | None = None) -> None:
        """Initialize with custom or default coding systems."""
        self._coding_systems = coding_systems or CODING_SYSTEMS

    def is_known_system(self, system_url: str) -> bool:
        """Check if a coding system URL is recognized."""
        return system_url in self._coding_systems

    def get_system_info(self, system_url: str) -> dict[str, str] | None:
        """Get information about a coding system."""
        return self._coding_systems.get(system_url)

    def get_system_name(self, system_url: str) -> str | None:
        """Get the human-readable name for a coding system."""
        info = self._coding_systems.get(system_url)
        return info.get("name") if info else None

    def validate_coding(
        self,
        coding: dict[str, Any],
        require_display: bool = False,
    ) -> list[str]:
        """
        Validate a FHIR Coding element.

        Args:
            coding: FHIR Coding element dict.
            require_display: Whether to require a display value.

        Returns:
            List of validation error messages (empty if valid).
        """
        errors = []

        # Check required fields
        if not coding.get("system"):
            errors.append("Coding.system is required")

        if not coding.get("code"):
            errors.append("Coding.code is required")

        if require_display and not coding.get("display"):
            errors.append("Coding.display is required")

        # Check if system is recognized (warning, not error)
        system = coding.get("system")
        if system and not self.is_known_system(system):
            # Not an error, just informational
            pass

        return errors

    def validate_codeable_concept(
        self,
        codeable_concept: dict[str, Any],
        require_coding: bool = True,
    ) -> list[str]:
        """
        Validate a FHIR CodeableConcept element.

        Args:
            codeable_concept: FHIR CodeableConcept element dict.
            require_coding: Whether to require at least one coding.

        Returns:
            List of validation error messages (empty if valid).
        """
        errors = []

        codings = codeable_concept.get("coding", [])

        if require_coding and not codings:
            # Must have at least coding or text
            if not codeable_concept.get("text"):
                errors.append(
                    "CodeableConcept must have at least one coding or text"
                )

        # Validate each coding
        for i, coding in enumerate(codings):
            coding_errors = self.validate_coding(coding)
            for error in coding_errors:
                errors.append(f"coding[{i}]: {error}")

        return errors

    def create_coding(
        self,
        system: str,
        code: str,
        display: str | None = None,
    ) -> dict[str, str]:
        """Create a properly formatted FHIR Coding element."""
        coding: dict[str, str] = {
            "system": system,
            "code": code,
        }
        if display:
            coding["display"] = display
        return coding

    def create_codeable_concept(
        self,
        system: str,
        code: str,
        display: str | None = None,
        text: str | None = None,
    ) -> dict[str, Any]:
        """Create a properly formatted FHIR CodeableConcept element."""
        concept: dict[str, Any] = {
            "coding": [self.create_coding(system, code, display)],
        }
        if text:
            concept["text"] = text
        return concept

    def create_observation_category(
        self, category_code: str
    ) -> dict[str, Any]:
        """Create an Observation category CodeableConcept."""
        display = OBSERVATION_CATEGORY_CODES.get(category_code, category_code)
        return self.create_codeable_concept(
            system="http://terminology.hl7.org/CodeSystem/observation-category",
            code=category_code,
            display=display,
        )

    def create_condition_category(
        self, category_code: str
    ) -> dict[str, Any]:
        """Create a Condition category CodeableConcept."""
        display = CONDITION_CATEGORY_CODES.get(category_code, category_code)
        return self.create_codeable_concept(
            system="http://terminology.hl7.org/CodeSystem/condition-category",
            code=category_code,
            display=display,
        )

    def get_loinc_vital_sign_info(self, code: str) -> dict[str, str] | None:
        """Get information about a LOINC vital sign code."""
        return LOINC_VITAL_SIGNS.get(code)

    def get_loinc_note_type_info(self, code: str) -> dict[str, str] | None:
        """Get information about a LOINC note type code."""
        return LOINC_NOTE_TYPES.get(code)


# Global validator instance
coding_system_validator = CodingSystemValidator()

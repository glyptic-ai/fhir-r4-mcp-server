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
    # Coverage Status (required)
    # https://hl7.org/fhir/R4/valueset-fm-status.html
    "coverage-status": [
        "active",
        "cancelled",
        "draft",
        "entered-in-error",
    ],
    # Related Person Relationship
    # https://hl7.org/fhir/R4/valueset-relatedperson-relationshiptype.html
    "relatedperson-relationship": [
        "FAMMEMB",  # Family Member
        "CHILD",  # Child
        "CHLDADOPT",  # Adopted child
        "CHLDFOST",  # Foster child
        "DAUC",  # Daughter
        "SONC",  # Son
        "STPCHLD",  # Step child
        "NCHILD",  # Natural child
        "PRN",  # Parent
        "ADOPTP",  # Adoptive parent
        "FTH",  # Father
        "MTH",  # Mother
        "NPRN",  # Natural parent
        "STPPRN",  # Step parent
        "SIB",  # Sibling
        "BRO",  # Brother
        "SIS",  # Sister
        "STPSIB",  # Step sibling
        "HSIB",  # Half-sibling
        "SIGOTHR",  # Significant other
        "SPS",  # Spouse
        "DOMPART",  # Domestic partner
        "FRND",  # Friend
        "NBOR",  # Neighbor
        "ROOM",  # Roommate
        "GUARD",  # Guardian
        "NOK",  # Next of Kin
        "POWATT",  # Power of Attorney
        "DPOWATT",  # Durable Power of Attorney
        "EMGCON",  # Emergency Contact
    ],
    # Appointment Status (required)
    # https://hl7.org/fhir/R4/valueset-appointmentstatus.html
    "appointment-status": [
        "proposed",
        "pending",
        "booked",
        "arrived",
        "fulfilled",
        "cancelled",
        "noshow",
        "entered-in-error",
        "checked-in",
        "waitlist",
    ],
    # Participant Required
    # https://hl7.org/fhir/R4/valueset-participantrequired.html
    "participant-required": [
        "required",
        "optional",
        "information-only",
    ],
    # Participation Status
    # https://hl7.org/fhir/R4/valueset-participationstatus.html
    "participation-status": [
        "accepted",
        "declined",
        "tentative",
        "needs-action",
    ],
    # Slot Status
    # https://hl7.org/fhir/R4/valueset-slotstatus.html
    "slot-status": [
        "busy",
        "free",
        "busy-unavailable",
        "busy-tentative",
        "entered-in-error",
    ],
    # Consent State
    # https://hl7.org/fhir/R4/valueset-consent-state-codes.html
    "consent-state": [
        "draft",
        "proposed",
        "active",
        "rejected",
        "inactive",
        "entered-in-error",
    ],
    # Consent Scope
    # https://hl7.org/fhir/R4/valueset-consent-scope.html
    "consent-scope": [
        "adr",  # Advanced Care Directive
        "research",  # Research
        "patient-privacy",  # Privacy Consent
        "treatment",  # Treatment
    ],
    # Consent Category
    # https://hl7.org/fhir/R4/valueset-consent-category.html
    "consent-category": [
        "acd",  # Advance Directive
        "dnr",  # Do Not Resuscitate
        "emrgonly",  # Emergency Only
        "hcd",  # Health Care Directive
        "npp",  # Notice of Privacy Practices
        "polst",  # POLST
        "research",  # Research Information Access
        "rsdid",  # De-identified Information Access
        "rsreid",  # Re-identifiable Information Access
    ],
    # QuestionnaireResponse Status
    # https://hl7.org/fhir/R4/valueset-questionnaire-answers-status.html
    "questionnaire-answers-status": [
        "in-progress",
        "completed",
        "amended",
        "entered-in-error",
        "stopped",
    ],
    # FamilyMemberHistory Status
    # https://hl7.org/fhir/R4/valueset-history-status.html
    "history-status": [
        "partial",
        "completed",
        "entered-in-error",
        "health-unknown",
    ],
    # Family Member Relationship (uses v3 RoleCode)
    # https://hl7.org/fhir/R4/v3/FamilyMember/vs.html
    "family-member-relationship": [
        "FAMMEMB",  # Family Member
        "CHILD",  # Child
        "CHLDADOPT",  # Adopted child
        "CHLDFOST",  # Foster child
        "CHLDINLAW",  # Child in-law
        "DAUC",  # Daughter
        "DAU",  # Natural daughter
        "DAUADOPT",  # Adopted daughter
        "DAUFOST",  # Foster daughter
        "STPDAU",  # Stepdaughter
        "DAUIN",  # Daughter in-law
        "SONC",  # Son
        "SON",  # Natural son
        "SONADOPT",  # Adopted son
        "SONFOST",  # Foster son
        "STPSON",  # Stepson
        "SONIN",  # Son in-law
        "STPCHLD",  # Step child
        "NCHILD",  # Natural child
        "PRN",  # Parent
        "ADOPTP",  # Adoptive parent
        "FTH",  # Father
        "NFTH",  # Natural father
        "STPFTH",  # Stepfather
        "FTHINLAW",  # Father-in-law
        "MTH",  # Mother
        "NMTH",  # Natural mother
        "STPMTH",  # Stepmother
        "MTHINLAW",  # Mother-in-law
        "NPRN",  # Natural parent
        "STPPRN",  # Step parent
        "SIB",  # Sibling
        "BRO",  # Brother
        "HBRO",  # Half-brother
        "NBRO",  # Natural brother
        "TWINBRO",  # Twin brother
        "FTWINBRO",  # Fraternal twin brother
        "ITWINBRO",  # Identical twin brother
        "STPBRO",  # Stepbrother
        "BROINLAW",  # Brother-in-law
        "SIS",  # Sister
        "HSIS",  # Half-sister
        "NSIS",  # Natural sister
        "TWINSIS",  # Twin sister
        "FTWINSIS",  # Fraternal twin sister
        "ITWINSIS",  # Identical twin sister
        "STPSIS",  # Stepsister
        "SISINLAW",  # Sister-in-law
        "STPSIB",  # Step sibling
        "HSIB",  # Half-sibling
        "NSIB",  # Natural sibling
        "GRPRN",  # Grandparent
        "GRMTH",  # Grandmother
        "GRFTH",  # Grandfather
        "GRNDCHILD",  # Grandchild
        "GRNDDAU",  # Granddaughter
        "GRNDSON",  # Grandson
        "AUNT",  # Aunt
        "UNCLE",  # Uncle
        "COUSN",  # Cousin
        "NIENEPH",  # Niece/Nephew
        "NIECE",  # Niece
        "NEPHEW",  # Nephew
        "EXT",  # Extended family member
        "SIGOTHR",  # Significant other
        "SPS",  # Spouse
        "HUSB",  # Husband
        "WIFE",  # Wife
        "DOMPART",  # Domestic partner
    ],
    # Subscription Status
    # https://hl7.org/fhir/R4/valueset-subscription-status.html
    "subscription-status": [
        "requested",
        "active",
        "error",
        "off",
    ],
    # Subscription Channel Type
    # https://hl7.org/fhir/R4/valueset-subscription-channel-type.html
    "subscription-channel-type": [
        "rest-hook",
        "websocket",
        "email",
        "sms",
        "message",
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
    "Coverage": {
        "status": "coverage-status",
    },
    "RelatedPerson": {
        "gender": "administrative-gender",
    },
    "Appointment": {
        "status": "appointment-status",
    },
    "Slot": {
        "status": "slot-status",
    },
    "Consent": {
        "status": "consent-state",
    },
    "QuestionnaireResponse": {
        "status": "questionnaire-answers-status",
    },
    "FamilyMemberHistory": {
        "status": "history-status",
    },
    "Subscription": {
        "status": "subscription-status",
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

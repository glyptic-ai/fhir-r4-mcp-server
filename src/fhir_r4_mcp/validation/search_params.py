"""FHIR R4 Search Parameter definitions and validation.

This module contains the standard search parameters for FHIR R4 resources
and provides validation for search queries.

See: https://hl7.org/fhir/R4/searchparameter-registry.html
"""

from dataclasses import dataclass
from typing import Any

from fhir_r4_mcp.utils.errors import FHIRValidationError


@dataclass
class ChainedParam:
    """Represents a parsed chained search parameter."""

    base_param: str  # e.g., "subject"
    target_type: str | None  # e.g., "Patient" (optional type discriminator)
    chained_param: str  # e.g., "name"
    full_chain: str  # Original string e.g., "subject:Patient.name"

# Common search parameters available on all resources
COMMON_SEARCH_PARAMS: list[str] = [
    "_id",
    "_lastUpdated",
    "_tag",
    "_profile",
    "_security",
    "_text",
    "_content",
    "_list",
    "_has",
    "_type",
    "_count",
    "_sort",
    "_include",
    "_revinclude",
    "_summary",
    "_elements",
    "_contained",
    "_containedType",
]

# Search parameters by resource type
# See: https://hl7.org/fhir/R4/searchparameter-registry.html
SEARCH_PARAMS: dict[str, list[str]] = {
    "Patient": [
        "active",
        "address",
        "address-city",
        "address-country",
        "address-postalcode",
        "address-state",
        "address-use",
        "birthdate",
        "death-date",
        "deceased",
        "email",
        "family",
        "gender",
        "general-practitioner",
        "given",
        "identifier",
        "language",
        "link",
        "name",
        "organization",
        "phone",
        "phonetic",
        "telecom",
    ],
    "Observation": [
        "based-on",
        "category",
        "code",
        "code-value-concept",
        "code-value-date",
        "code-value-quantity",
        "code-value-string",
        "combo-code",
        "combo-code-value-concept",
        "combo-code-value-quantity",
        "combo-data-absent-reason",
        "combo-value-concept",
        "combo-value-quantity",
        "component-code",
        "component-code-value-concept",
        "component-code-value-quantity",
        "component-data-absent-reason",
        "component-value-concept",
        "component-value-quantity",
        "data-absent-reason",
        "date",
        "derived-from",
        "device",
        "encounter",
        "focus",
        "has-member",
        "identifier",
        "method",
        "part-of",
        "patient",
        "performer",
        "specimen",
        "status",
        "subject",
        "value-concept",
        "value-date",
        "value-quantity",
        "value-string",
    ],
    "Condition": [
        "abatement-age",
        "abatement-date",
        "abatement-string",
        "asserter",
        "body-site",
        "category",
        "clinical-status",
        "code",
        "encounter",
        "evidence",
        "evidence-detail",
        "identifier",
        "onset-age",
        "onset-date",
        "onset-info",
        "patient",
        "recorded-date",
        "severity",
        "stage",
        "subject",
        "verification-status",
    ],
    "MedicationRequest": [
        "authoredon",
        "category",
        "code",
        "date",
        "encounter",
        "identifier",
        "intended-dispenser",
        "intended-performer",
        "intended-performertype",
        "intent",
        "medication",
        "patient",
        "priority",
        "requester",
        "status",
        "subject",
    ],
    "Encounter": [
        "account",
        "appointment",
        "based-on",
        "class",
        "date",
        "diagnosis",
        "episode-of-care",
        "identifier",
        "length",
        "location",
        "location-period",
        "part-of",
        "participant",
        "participant-type",
        "patient",
        "practitioner",
        "reason-code",
        "reason-reference",
        "service-provider",
        "special-arrangement",
        "status",
        "subject",
        "type",
    ],
    "AllergyIntolerance": [
        "asserter",
        "category",
        "clinical-status",
        "code",
        "criticality",
        "date",
        "identifier",
        "last-date",
        "manifestation",
        "onset",
        "patient",
        "recorder",
        "route",
        "severity",
        "type",
        "verification-status",
    ],
    "CarePlan": [
        "activity-code",
        "activity-date",
        "activity-reference",
        "based-on",
        "care-team",
        "category",
        "condition",
        "date",
        "encounter",
        "goal",
        "identifier",
        "instantiates-canonical",
        "instantiates-uri",
        "intent",
        "part-of",
        "patient",
        "performer",
        "replaces",
        "status",
        "subject",
    ],
    "CareTeam": [
        "category",
        "date",
        "encounter",
        "identifier",
        "participant",
        "patient",
        "status",
        "subject",
    ],
    "DiagnosticReport": [
        "based-on",
        "category",
        "code",
        "conclusion",
        "date",
        "encounter",
        "identifier",
        "issued",
        "media",
        "patient",
        "performer",
        "result",
        "results-interpreter",
        "specimen",
        "status",
        "subject",
    ],
    "DocumentReference": [
        "authenticator",
        "author",
        "category",
        "contenttype",
        "custodian",
        "date",
        "description",
        "encounter",
        "event",
        "facility",
        "format",
        "identifier",
        "language",
        "location",
        "patient",
        "period",
        "related",
        "relatesto",
        "relation",
        "relationship",
        "security-label",
        "setting",
        "status",
        "subject",
        "type",
    ],
    "Goal": [
        "achievement-status",
        "category",
        "identifier",
        "lifecycle-status",
        "patient",
        "start-date",
        "subject",
        "target-date",
    ],
    "Immunization": [
        "date",
        "identifier",
        "location",
        "lot-number",
        "manufacturer",
        "patient",
        "performer",
        "reaction",
        "reaction-date",
        "reason-code",
        "reason-reference",
        "series",
        "status",
        "status-reason",
        "target-disease",
        "vaccine-code",
    ],
    "Medication": [
        "code",
        "expiration-date",
        "form",
        "identifier",
        "ingredient",
        "ingredient-code",
        "lot-number",
        "manufacturer",
        "status",
    ],
    "MedicationStatement": [
        "category",
        "code",
        "context",
        "effective",
        "identifier",
        "medication",
        "part-of",
        "patient",
        "source",
        "status",
        "subject",
    ],
    "Practitioner": [
        "active",
        "address",
        "address-city",
        "address-country",
        "address-postalcode",
        "address-state",
        "address-use",
        "communication",
        "email",
        "family",
        "gender",
        "given",
        "identifier",
        "name",
        "phone",
        "phonetic",
        "telecom",
    ],
    "Procedure": [
        "based-on",
        "category",
        "code",
        "date",
        "encounter",
        "identifier",
        "instantiates-canonical",
        "instantiates-uri",
        "location",
        "part-of",
        "patient",
        "performer",
        "reason-code",
        "reason-reference",
        "status",
        "subject",
    ],
    "ServiceRequest": [
        "authored",
        "based-on",
        "body-site",
        "category",
        "code",
        "encounter",
        "identifier",
        "instantiates-canonical",
        "instantiates-uri",
        "intent",
        "occurrence",
        "patient",
        "performer",
        "performer-type",
        "priority",
        "replaces",
        "requester",
        "requisition",
        "specimen",
        "status",
        "subject",
    ],
    "Organization": [
        "active",
        "address",
        "address-city",
        "address-country",
        "address-postalcode",
        "address-state",
        "address-use",
        "endpoint",
        "identifier",
        "name",
        "partof",
        "phonetic",
        "type",
    ],
    "Location": [
        "address",
        "address-city",
        "address-country",
        "address-postalcode",
        "address-state",
        "address-use",
        "endpoint",
        "identifier",
        "name",
        "near",
        "operational-status",
        "organization",
        "partof",
        "status",
        "type",
    ],
    "Device": [
        "device-name",
        "identifier",
        "location",
        "manufacturer",
        "model",
        "organization",
        "patient",
        "status",
        "type",
        "udi-carrier",
        "udi-di",
        "url",
    ],
    "Group": [
        "actual",
        "characteristic",
        "characteristic-value",
        "code",
        "exclude",
        "identifier",
        "managing-entity",
        "member",
        "type",
        "value",
    ],
    "Provenance": [
        "agent",
        "agent-role",
        "agent-type",
        "entity",
        "location",
        "patient",
        "recorded",
        "signature-type",
        "target",
        "when",
    ],
    "Coverage": [
        "beneficiary",
        "class-type",
        "class-value",
        "dependent",
        "identifier",
        "patient",
        "payor",
        "policy-holder",
        "status",
        "subscriber",
        "type",
    ],
    "RelatedPerson": [
        "active",
        "address",
        "address-city",
        "address-country",
        "address-postalcode",
        "address-state",
        "address-use",
        "birthdate",
        "email",
        "gender",
        "identifier",
        "name",
        "patient",
        "phone",
        "phonetic",
        "relationship",
        "telecom",
    ],
    "Appointment": [
        "actor",
        "appointment-type",
        "based-on",
        "date",
        "identifier",
        "location",
        "part-status",
        "patient",
        "practitioner",
        "reason-code",
        "reason-reference",
        "service-category",
        "service-type",
        "slot",
        "specialty",
        "status",
        "supporting-info",
    ],
    "Schedule": [
        "active",
        "actor",
        "date",
        "identifier",
        "service-category",
        "service-type",
        "specialty",
    ],
    "Slot": [
        "appointment-type",
        "identifier",
        "schedule",
        "service-category",
        "service-type",
        "specialty",
        "start",
        "status",
    ],
    "Consent": [
        "action",
        "actor",
        "category",
        "consentor",
        "data",
        "date",
        "identifier",
        "organization",
        "patient",
        "period",
        "purpose",
        "scope",
        "security-label",
        "source-reference",
        "status",
    ],
    "QuestionnaireResponse": [
        "author",
        "authored",
        "based-on",
        "encounter",
        "identifier",
        "item-subject",
        "part-of",
        "patient",
        "questionnaire",
        "source",
        "status",
        "subject",
    ],
    "FamilyMemberHistory": [
        "code",
        "date",
        "identifier",
        "instantiates-canonical",
        "instantiates-uri",
        "patient",
        "relationship",
        "sex",
        "status",
    ],
    "Subscription": [
        "contact",
        "criteria",
        "payload",
        "status",
        "type",
        "url",
    ],
}

# Search parameter modifiers
# See: https://hl7.org/fhir/R4/search.html#modifiers
SEARCH_MODIFIERS: dict[str, list[str]] = {
    "string": ["exact", "contains"],
    "reference": ["identifier", "type"],
    "uri": ["below", "above"],
    "token": ["text", "not", "above", "below", "in", "not-in", "of-type"],
    "date": [],
    "number": [],
    "quantity": [],
}

# Prefix modifiers for number, date, quantity
# See: https://hl7.org/fhir/R4/search.html#prefix
SEARCH_PREFIXES: list[str] = [
    "eq",  # equal (default)
    "ne",  # not equal
    "lt",  # less than
    "gt",  # greater than
    "le",  # less than or equal
    "ge",  # greater than or equal
    "sa",  # starts after
    "eb",  # ends before
    "ap",  # approximately
]


class SearchParamValidator:
    """Validator for FHIR search parameters."""

    def __init__(
        self,
        search_params: dict[str, list[str]] | None = None,
        common_params: list[str] | None = None,
    ) -> None:
        """Initialize with custom or default search parameters."""
        self._search_params = search_params or SEARCH_PARAMS
        self._common_params = common_params or COMMON_SEARCH_PARAMS

    def get_valid_params(self, resource_type: str) -> list[str]:
        """Get all valid search parameters for a resource type."""
        resource_params = self._search_params.get(resource_type, [])
        return self._common_params + resource_params

    def is_valid_param(self, resource_type: str, param_name: str) -> bool:
        """
        Check if a search parameter is valid for a resource type.

        Args:
            resource_type: FHIR resource type.
            param_name: Search parameter name (without modifiers).

        Returns:
            True if valid, False otherwise.
        """
        # Strip any modifiers (e.g., :exact, :contains)
        base_param = param_name.split(":")[0]

        # Check common params
        if base_param in self._common_params:
            return True

        # Check resource-specific params
        resource_params = self._search_params.get(resource_type, [])
        return base_param in resource_params

    def validate_search_params(
        self,
        resource_type: str,
        params: dict[str, Any],
        raise_on_error: bool = False,
    ) -> list[str]:
        """
        Validate search parameters for a resource type.

        Args:
            resource_type: FHIR resource type.
            params: Search parameters dictionary.
            raise_on_error: If True, raise exception on first invalid param.

        Returns:
            List of invalid parameter names.

        Raises:
            FHIRValidationError: If raise_on_error=True and invalid params found.
        """
        invalid_params = []

        for param_name in params.keys():
            if not self.is_valid_param(resource_type, param_name):
                invalid_params.append(param_name)
                if raise_on_error:
                    valid_params = self.get_valid_params(resource_type)
                    raise FHIRValidationError(
                        message=f"Invalid search parameter '{param_name}' for {resource_type}",
                        field=param_name,
                        details={
                            "resource_type": resource_type,
                            "valid_params": valid_params[:20],  # Truncate for readability
                        },
                        suggestion=f"Use one of the valid search parameters for {resource_type}",
                    )

        return invalid_params

    def validate_modifier(
        self,
        param_name: str,
        param_type: str = "string",
    ) -> bool:
        """
        Validate a search parameter modifier.

        Args:
            param_name: Full parameter name including modifier (e.g., "name:exact").
            param_type: Type of the search parameter.

        Returns:
            True if modifier is valid or no modifier present.
        """
        if ":" not in param_name:
            return True

        parts = param_name.split(":")
        if len(parts) != 2:
            return False

        modifier = parts[1]
        valid_modifiers = SEARCH_MODIFIERS.get(param_type, [])

        # Also allow 'missing' modifier on all types
        return modifier in valid_modifiers or modifier == "missing"

    def parse_date_prefix(self, value: str) -> tuple[str, str]:
        """
        Parse a date value with optional prefix.

        Args:
            value: Date value potentially with prefix (e.g., "ge2024-01-01").

        Returns:
            Tuple of (prefix, date_value). Prefix is "eq" if not specified.
        """
        for prefix in SEARCH_PREFIXES:
            if value.startswith(prefix):
                return prefix, value[len(prefix) :]

        return "eq", value


# Reference parameter to target types mapping
# Maps reference parameters to the resource types they can target
REFERENCE_TARGET_TYPES: dict[str, dict[str, list[str]]] = {
    "Observation": {
        "subject": ["Patient", "Group", "Device", "Location"],
        "patient": ["Patient"],
        "performer": ["Practitioner", "PractitionerRole", "Organization", "CareTeam", "Patient", "RelatedPerson"],
        "encounter": ["Encounter"],
    },
    "Condition": {
        "subject": ["Patient", "Group"],
        "patient": ["Patient"],
        "encounter": ["Encounter"],
        "asserter": ["Practitioner", "PractitionerRole", "Patient", "RelatedPerson"],
    },
    "MedicationRequest": {
        "subject": ["Patient", "Group"],
        "patient": ["Patient"],
        "encounter": ["Encounter"],
        "requester": ["Practitioner", "PractitionerRole", "Organization", "Patient", "RelatedPerson", "Device"],
    },
    "Encounter": {
        "subject": ["Patient", "Group"],
        "patient": ["Patient"],
        "practitioner": ["Practitioner"],
        "participant": ["Practitioner", "PractitionerRole", "RelatedPerson"],
    },
    "DiagnosticReport": {
        "subject": ["Patient", "Group", "Device", "Location"],
        "patient": ["Patient"],
        "encounter": ["Encounter"],
        "performer": ["Practitioner", "PractitionerRole", "Organization", "CareTeam"],
    },
    "Procedure": {
        "subject": ["Patient", "Group"],
        "patient": ["Patient"],
        "encounter": ["Encounter"],
        "performer": ["Practitioner", "PractitionerRole", "Organization", "Patient", "RelatedPerson", "Device"],
    },
    "CarePlan": {
        "subject": ["Patient", "Group"],
        "patient": ["Patient"],
        "encounter": ["Encounter"],
        "performer": ["Practitioner", "PractitionerRole", "Organization", "CareTeam", "Patient", "RelatedPerson", "Device"],
    },
    "DocumentReference": {
        "subject": ["Patient", "Practitioner", "Group", "Device"],
        "patient": ["Patient"],
        "encounter": ["Encounter"],
        "author": ["Practitioner", "PractitionerRole", "Organization", "Device", "Patient", "RelatedPerson"],
    },
}


class ChainedSearchParser:
    """Parse and validate chained search parameters.

    Chained search allows querying across resource references, like:
    - Observation?subject:Patient.name=smith
    - MedicationRequest?subject:Patient.birthdate=1990-01-01
    - Condition?subject:Patient.identifier=12345

    See: https://hl7.org/fhir/R4/search.html#chaining
    """

    def __init__(
        self,
        search_params: dict[str, list[str]] | None = None,
        reference_targets: dict[str, dict[str, list[str]]] | None = None,
    ) -> None:
        """Initialize the parser."""
        self._search_params = search_params or SEARCH_PARAMS
        self._reference_targets = reference_targets or REFERENCE_TARGET_TYPES

    def parse(self, param: str) -> ChainedParam | None:
        """
        Parse a chained search parameter.

        Args:
            param: Parameter string like "subject:Patient.name" or "patient.birthdate"

        Returns:
            ChainedParam if valid chain, None if not a chained parameter
        """
        # Check for explicit type discriminator (e.g., subject:Patient.name)
        if ":" in param and "." in param:
            colon_idx = param.index(":")
            dot_idx = param.index(".", colon_idx)

            base_param = param[:colon_idx]
            target_type = param[colon_idx + 1 : dot_idx]
            chained_param = param[dot_idx + 1 :]

            return ChainedParam(
                base_param=base_param,
                target_type=target_type,
                chained_param=chained_param,
                full_chain=param,
            )

        # Check for simple chain without type (e.g., patient.name)
        if "." in param and ":" not in param:
            dot_idx = param.index(".")
            base_param = param[:dot_idx]
            chained_param = param[dot_idx + 1 :]

            return ChainedParam(
                base_param=base_param,
                target_type=None,
                chained_param=chained_param,
                full_chain=param,
            )

        return None

    def validate_chain(
        self,
        resource_type: str,
        chain: ChainedParam,
        raise_on_error: bool = False,
    ) -> list[str]:
        """
        Validate a chained search parameter for a resource type.

        Args:
            resource_type: The base resource type being searched
            chain: Parsed chained parameter
            raise_on_error: If True, raise exception on first error

        Returns:
            List of validation error messages
        """
        errors: list[str] = []

        # Check if base parameter exists for the resource type
        resource_params = self._search_params.get(resource_type, [])
        if chain.base_param not in resource_params:
            error = f"Invalid base parameter '{chain.base_param}' for {resource_type}"
            errors.append(error)
            if raise_on_error:
                raise FHIRValidationError(message=error, field=chain.full_chain)

        # Determine target types for the reference parameter
        resource_targets = self._reference_targets.get(resource_type, {})
        allowed_targets = resource_targets.get(chain.base_param, [])

        # If explicit type provided, validate it's allowed
        if chain.target_type:
            if allowed_targets and chain.target_type not in allowed_targets:
                error = (
                    f"Target type '{chain.target_type}' not valid for "
                    f"{resource_type}.{chain.base_param}. "
                    f"Allowed: {allowed_targets}"
                )
                errors.append(error)
                if raise_on_error:
                    raise FHIRValidationError(message=error, field=chain.full_chain)

            # Validate chained parameter exists on target type
            target_params = self._search_params.get(chain.target_type, [])
            # Strip any modifier from chained param
            base_chained = chain.chained_param.split(":")[0]
            if target_params and base_chained not in target_params:
                error = (
                    f"Invalid chained parameter '{chain.chained_param}' "
                    f"for target type {chain.target_type}"
                )
                errors.append(error)
                if raise_on_error:
                    raise FHIRValidationError(message=error, field=chain.full_chain)

        return errors

    def get_target_types(
        self,
        resource_type: str,
        reference_param: str,
    ) -> list[str]:
        """Get allowed target types for a reference parameter."""
        resource_targets = self._reference_targets.get(resource_type, {})
        return resource_targets.get(reference_param, [])


# Global validator instance
search_param_validator = SearchParamValidator()

# Global chained search parser instance
chained_search_parser = ChainedSearchParser()

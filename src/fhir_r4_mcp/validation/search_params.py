"""FHIR R4 Search Parameter definitions and validation.

This module contains the standard search parameters for FHIR R4 resources
and provides validation for search queries.

See: https://hl7.org/fhir/R4/searchparameter-registry.html
"""

from typing import Any

from fhir_r4_mcp.utils.errors import FHIRValidationError

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


# Global validator instance
search_param_validator = SearchParamValidator()

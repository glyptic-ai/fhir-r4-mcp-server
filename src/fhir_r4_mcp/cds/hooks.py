"""CDS Hooks data structures.

This module defines the data structures for CDS Hooks integration
following the CDS Hooks 2.0 specification.

See: https://cds-hooks.hl7.org/2.0/
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class HookType(str, Enum):
    """Standard CDS Hook types.

    See: https://cds-hooks.hl7.org/hooks/
    """

    PATIENT_VIEW = "patient-view"  # When patient chart is opened
    MEDICATION_PRESCRIBE = "medication-prescribe"  # When prescribing medication
    ORDER_SELECT = "order-select"  # When selecting orders
    ORDER_SIGN = "order-sign"  # When signing orders
    ENCOUNTER_START = "encounter-start"  # When encounter starts
    ENCOUNTER_DISCHARGE = "encounter-discharge"  # When discharging patient
    APPOINTMENT_BOOK = "appointment-book"  # When booking appointment


class CardIndicator(str, Enum):
    """Card urgency indicators."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class SelectionBehavior(str, Enum):
    """Suggestion selection behavior."""

    AT_MOST_ONE = "at-most-one"  # User can select at most one
    ANY = "any"  # User can select any number


@dataclass
class CDSLink:
    """A link to additional information.

    Links can be absolute URLs or SMART app launch URLs.
    """

    label: str
    url: str
    type: str = "absolute"  # absolute | smart
    app_context: str | None = None  # Context to pass to SMART app

    def to_dict(self) -> dict[str, Any]:
        """Convert to CDS Hooks format."""
        link: dict[str, Any] = {
            "label": self.label,
            "url": self.url,
            "type": self.type,
        }
        if self.app_context:
            link["appContext"] = self.app_context
        return link


@dataclass
class CDSAction:
    """An action for a suggestion.

    Actions modify FHIR resources when a suggestion is accepted.
    """

    type: str  # create | update | delete
    description: str
    resource: dict[str, Any] | None = None  # FHIR resource
    resource_id: str | None = None  # For update/delete

    def to_dict(self) -> dict[str, Any]:
        """Convert to CDS Hooks format."""
        action: dict[str, Any] = {
            "type": self.type,
            "description": self.description,
        }
        if self.resource:
            action["resource"] = self.resource
        if self.resource_id:
            action["resourceId"] = self.resource_id
        return action


@dataclass
class CDSSuggestion:
    """A suggestion for action.

    Suggestions are actionable recommendations that can be
    accepted by the user to modify FHIR resources.
    """

    label: str
    uuid: str | None = None
    is_recommended: bool = False
    actions: list[CDSAction] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to CDS Hooks format."""
        suggestion: dict[str, Any] = {
            "label": self.label,
        }
        if self.uuid:
            suggestion["uuid"] = self.uuid
        if self.is_recommended:
            suggestion["isRecommended"] = True
        if self.actions:
            suggestion["actions"] = [a.to_dict() for a in self.actions]
        return suggestion


@dataclass
class CDSCard:
    """A decision support card.

    Cards are the primary unit of response from CDS Hooks services,
    containing information, warnings, or recommendations.
    """

    summary: str  # Short summary (max ~140 chars)
    indicator: CardIndicator = CardIndicator.INFO
    source: dict[str, Any] = field(default_factory=lambda: {"label": "CDS Service"})
    detail: str | None = None  # Markdown detail text
    suggestions: list[CDSSuggestion] = field(default_factory=list)
    selection_behavior: SelectionBehavior | None = None
    links: list[CDSLink] = field(default_factory=list)
    override_reasons: list[dict[str, str]] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to CDS Hooks format."""
        card: dict[str, Any] = {
            "summary": self.summary,
            "indicator": self.indicator.value,
            "source": self.source,
        }
        if self.detail:
            card["detail"] = self.detail
        if self.suggestions:
            card["suggestions"] = [s.to_dict() for s in self.suggestions]
        if self.selection_behavior:
            card["selectionBehavior"] = self.selection_behavior.value
        if self.links:
            card["links"] = [link.to_dict() for link in self.links]
        if self.override_reasons:
            card["overrideReasons"] = self.override_reasons
        return card


@dataclass
class CDSHook:
    """Definition of a CDS Hook.

    Describes a hook that can be invoked by EHR systems.
    """

    id: str  # Hook identifier
    hook: HookType  # Hook type
    title: str  # Human-readable title
    description: str  # Description
    prefetch: dict[str, str] = field(default_factory=dict)  # Prefetch templates
    usage_requirements: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to CDS Hooks discovery format."""
        hook: dict[str, Any] = {
            "id": self.id,
            "hook": self.hook.value,
            "title": self.title,
            "description": self.description,
        }
        if self.prefetch:
            hook["prefetch"] = self.prefetch
        if self.usage_requirements:
            hook["usageRequirements"] = self.usage_requirements
        return hook


@dataclass
class CDSHookRequest:
    """A CDS Hook invocation request.

    Sent by the EHR when a hook is triggered.
    """

    hook: str  # Hook type that was triggered
    hook_instance: str  # UUID for this specific invocation
    context: dict[str, Any]  # Hook-specific context
    prefetch: dict[str, Any] = field(default_factory=dict)  # Pre-fetched FHIR resources
    fhir_server: str | None = None  # FHIR server base URL
    fhir_authorization: dict[str, str] | None = None  # OAuth token info

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CDSHookRequest":
        """Parse from CDS Hooks request format."""
        return cls(
            hook=data.get("hook", ""),
            hook_instance=data.get("hookInstance", ""),
            context=data.get("context", {}),
            prefetch=data.get("prefetch", {}),
            fhir_server=data.get("fhirServer"),
            fhir_authorization=data.get("fhirAuthorization"),
        )

    def get_patient_id(self) -> str | None:
        """Extract patient ID from context."""
        # Try various common context fields
        patient_id = self.context.get("patientId")
        if not patient_id:
            patient_id = self.context.get("patient")
        if not patient_id:
            # Check userId (might be patient in patient-facing apps)
            user_id = self.context.get("userId")
            if user_id and user_id.startswith("Patient/"):
                patient_id = user_id.replace("Patient/", "")
        return patient_id

    def get_user_id(self) -> str | None:
        """Extract user ID from context."""
        return self.context.get("userId")

    def get_encounter_id(self) -> str | None:
        """Extract encounter ID from context."""
        encounter_id = self.context.get("encounterId")
        if not encounter_id:
            encounter_id = self.context.get("encounter")
        return encounter_id


@dataclass
class CDSHookResponse:
    """A CDS Hook invocation response.

    Contains cards with recommendations and optional system actions.
    """

    cards: list[CDSCard] = field(default_factory=list)
    system_actions: list[CDSAction] = field(default_factory=list)
    extension: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to CDS Hooks response format."""
        response: dict[str, Any] = {
            "cards": [card.to_dict() for card in self.cards],
        }
        if self.system_actions:
            response["systemActions"] = [a.to_dict() for a in self.system_actions]
        if self.extension:
            response["extension"] = self.extension
        return response

    def add_card(
        self,
        summary: str,
        indicator: CardIndicator = CardIndicator.INFO,
        detail: str | None = None,
        source_label: str = "CDS Service",
        source_url: str | None = None,
    ) -> CDSCard:
        """Add a card to the response.

        Args:
            summary: Card summary
            indicator: Urgency indicator
            detail: Markdown detail text
            source_label: Source label
            source_url: Source URL

        Returns:
            The created card
        """
        source: dict[str, Any] = {"label": source_label}
        if source_url:
            source["url"] = source_url

        card = CDSCard(
            summary=summary,
            indicator=indicator,
            detail=detail,
            source=source,
        )
        self.cards.append(card)
        return card

    def add_info_card(self, summary: str, detail: str | None = None) -> CDSCard:
        """Add an informational card."""
        return self.add_card(summary, CardIndicator.INFO, detail)

    def add_warning_card(self, summary: str, detail: str | None = None) -> CDSCard:
        """Add a warning card."""
        return self.add_card(summary, CardIndicator.WARNING, detail)

    def add_critical_card(self, summary: str, detail: str | None = None) -> CDSCard:
        """Add a critical alert card."""
        return self.add_card(summary, CardIndicator.CRITICAL, detail)


# Common context fields by hook type
HOOK_CONTEXT_FIELDS: dict[HookType, list[str]] = {
    HookType.PATIENT_VIEW: ["userId", "patientId", "encounterId"],
    HookType.MEDICATION_PRESCRIBE: ["userId", "patientId", "encounterId", "medications", "draftOrders"],
    HookType.ORDER_SELECT: ["userId", "patientId", "encounterId", "selections", "draftOrders"],
    HookType.ORDER_SIGN: ["userId", "patientId", "encounterId", "draftOrders"],
    HookType.ENCOUNTER_START: ["userId", "patientId", "encounterId"],
    HookType.ENCOUNTER_DISCHARGE: ["userId", "patientId", "encounterId"],
    HookType.APPOINTMENT_BOOK: ["userId", "patientId", "encounterId", "appointments"],
}

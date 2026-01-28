"""FHIR R4 AuditEvent data structures.

This module defines the data structures for HIPAA-compliant audit logging
based on the FHIR R4 AuditEvent resource.

See: https://hl7.org/fhir/R4/auditevent.html
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class AuditType(str, Enum):
    """AuditEvent type codes."""

    REST = "rest"  # RESTful operation
    EXPORT = "export"  # Bulk data export
    QUERY = "query"  # Search query
    IMPORT = "import"  # Data import
    TRANSMIT = "transmit"  # Data transmission


class AuditSubtype(str, Enum):
    """AuditEvent subtype codes (FHIR REST interactions)."""

    READ = "read"
    VREAD = "vread"
    UPDATE = "update"
    PATCH = "patch"
    DELETE = "delete"
    HISTORY = "history"
    CREATE = "create"
    SEARCH = "search"
    CAPABILITIES = "capabilities"
    TRANSACTION = "transaction"
    BATCH = "batch"
    OPERATION = "operation"


class AuditAction(str, Enum):
    """AuditEvent action codes.

    See: https://hl7.org/fhir/R4/valueset-audit-event-action.html
    """

    CREATE = "C"  # Create
    READ = "R"  # Read/View/Print
    UPDATE = "U"  # Update
    DELETE = "D"  # Delete
    EXECUTE = "E"  # Execute


class AuditOutcome(str, Enum):
    """AuditEvent outcome codes.

    See: https://hl7.org/fhir/R4/valueset-audit-event-outcome.html
    """

    SUCCESS = "0"  # Success
    MINOR_FAILURE = "4"  # Minor failure
    SERIOUS_FAILURE = "8"  # Serious failure
    MAJOR_FAILURE = "12"  # Major failure


@dataclass
class AuditAgent:
    """Who performed the action.

    Represents the user, system, or application that initiated the action.
    """

    who: str  # User or system identifier
    name: str | None = None  # Display name
    type_code: str | None = None  # User type code
    role: list[str] = field(default_factory=list)  # Role codes
    requestor: bool = True  # Whether this agent initiated the request
    network_address: str | None = None  # IP address or hostname
    network_type: str | None = None  # Network type (1=name, 2=IP, 5=URI)

    def to_fhir(self) -> dict[str, Any]:
        """Convert to FHIR AuditEvent.agent format."""
        agent: dict[str, Any] = {
            "who": {"display": self.who},
            "requestor": self.requestor,
        }

        if self.name:
            agent["name"] = self.name
            agent["who"]["display"] = self.name

        if self.type_code:
            agent["type"] = {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationType",
                        "code": self.type_code,
                    }
                ]
            }

        if self.role:
            agent["role"] = [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
                            "code": role,
                        }
                    ]
                }
                for role in self.role
            ]

        if self.network_address:
            agent["network"] = {
                "address": self.network_address,
                "type": self.network_type or "2",  # Default to IP address
            }

        return agent


@dataclass
class AuditSource:
    """The system that recorded the audit event."""

    site: str | None = None  # Site identifier
    observer: str = "FHIR-R4-MCP-Server"  # System identifier
    type_codes: list[str] = field(default_factory=lambda: ["4"])  # Source type codes

    def to_fhir(self) -> dict[str, Any]:
        """Convert to FHIR AuditEvent.source format."""
        source: dict[str, Any] = {
            "observer": {"display": self.observer},
        }

        if self.site:
            source["site"] = self.site

        if self.type_codes:
            source["type"] = [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/security-source-type",
                    "code": code,
                }
                for code in self.type_codes
            ]

        return source


@dataclass
class AuditEntity:
    """What was accessed or modified."""

    what: str  # Resource reference (e.g., "Patient/123")
    type_code: str | None = None  # Entity type code
    role_code: str | None = None  # Entity role code
    name: str | None = None  # Entity name
    description: str | None = None  # Description
    query: str | None = None  # Query string (base64 encoded)
    detail: dict[str, str] = field(default_factory=dict)  # Additional details

    def to_fhir(self) -> dict[str, Any]:
        """Convert to FHIR AuditEvent.entity format."""
        entity: dict[str, Any] = {
            "what": {"reference": self.what},
        }

        if self.type_code:
            entity["type"] = {
                "system": "http://terminology.hl7.org/CodeSystem/audit-entity-type",
                "code": self.type_code,
            }

        if self.role_code:
            entity["role"] = {
                "system": "http://terminology.hl7.org/CodeSystem/object-role",
                "code": self.role_code,
            }

        if self.name:
            entity["name"] = self.name

        if self.description:
            entity["description"] = self.description

        if self.query:
            entity["query"] = self.query

        if self.detail:
            entity["detail"] = [
                {"type": key, "valueString": value} for key, value in self.detail.items()
            ]

        return entity


@dataclass
class AuditEvent:
    """HIPAA-compliant audit event.

    Represents a FHIR AuditEvent resource for logging access to PHI.

    See: https://hl7.org/fhir/R4/auditevent.html
    """

    type: AuditType
    subtype: AuditSubtype
    action: AuditAction
    outcome: AuditOutcome
    recorded: datetime = field(default_factory=datetime.utcnow)
    agent: AuditAgent | None = None
    source: AuditSource = field(default_factory=AuditSource)
    entity: list[AuditEntity] = field(default_factory=list)
    outcome_desc: str | None = None
    purpose_of_event: list[str] = field(default_factory=list)
    period_start: datetime | None = None
    period_end: datetime | None = None

    def to_fhir(self) -> dict[str, Any]:
        """Convert to FHIR AuditEvent resource format."""
        event: dict[str, Any] = {
            "resourceType": "AuditEvent",
            "type": {
                "system": "http://terminology.hl7.org/CodeSystem/audit-event-type",
                "code": self.type.value,
                "display": self.type.name,
            },
            "subtype": [
                {
                    "system": "http://hl7.org/fhir/restful-interaction",
                    "code": self.subtype.value,
                    "display": self.subtype.name,
                }
            ],
            "action": self.action.value,
            "recorded": self.recorded.isoformat() + "Z",
            "outcome": self.outcome.value,
            "source": self.source.to_fhir(),
        }

        if self.outcome_desc:
            event["outcomeDesc"] = self.outcome_desc

        if self.agent:
            event["agent"] = [self.agent.to_fhir()]
        else:
            # Default agent
            event["agent"] = [
                {
                    "who": {"display": "Unknown"},
                    "requestor": True,
                }
            ]

        if self.entity:
            event["entity"] = [e.to_fhir() for e in self.entity]

        if self.purpose_of_event:
            event["purposeOfEvent"] = [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v3-ActReason",
                            "code": purpose,
                        }
                    ]
                }
                for purpose in self.purpose_of_event
            ]

        if self.period_start:
            event["period"] = {"start": self.period_start.isoformat() + "Z"}
            if self.period_end:
                event["period"]["end"] = self.period_end.isoformat() + "Z"

        return event

    def to_dict(self) -> dict[str, Any]:
        """Convert to simplified dictionary format for logging."""
        return {
            "type": self.type.value,
            "subtype": self.subtype.value,
            "action": self.action.value,
            "outcome": self.outcome.value,
            "recorded": self.recorded.isoformat() + "Z",
            "agent": self.agent.who if self.agent else None,
            "source": self.source.observer,
            "entities": [e.what for e in self.entity],
            "outcome_desc": self.outcome_desc,
        }


def create_audit_event(
    subtype: AuditSubtype,
    outcome: AuditOutcome,
    connection_id: str,
    resource_type: str | None = None,
    resource_id: str | None = None,
    query: str | None = None,
    outcome_desc: str | None = None,
    user: str | None = None,
) -> AuditEvent:
    """Factory function to create an audit event.

    Args:
        subtype: The FHIR interaction subtype
        outcome: The outcome of the operation
        connection_id: The FHIR connection ID
        resource_type: The resource type accessed
        resource_id: The resource ID accessed
        query: Search query string
        outcome_desc: Description of outcome
        user: User identifier

    Returns:
        Configured AuditEvent
    """
    # Determine action from subtype
    action_map = {
        AuditSubtype.CREATE: AuditAction.CREATE,
        AuditSubtype.READ: AuditAction.READ,
        AuditSubtype.VREAD: AuditAction.READ,
        AuditSubtype.UPDATE: AuditAction.UPDATE,
        AuditSubtype.PATCH: AuditAction.UPDATE,
        AuditSubtype.DELETE: AuditAction.DELETE,
        AuditSubtype.HISTORY: AuditAction.READ,
        AuditSubtype.SEARCH: AuditAction.READ,
        AuditSubtype.CAPABILITIES: AuditAction.READ,
        AuditSubtype.TRANSACTION: AuditAction.EXECUTE,
        AuditSubtype.BATCH: AuditAction.EXECUTE,
        AuditSubtype.OPERATION: AuditAction.EXECUTE,
    }
    action = action_map.get(subtype, AuditAction.READ)

    # Determine event type
    event_type = AuditType.REST
    if subtype == AuditSubtype.SEARCH:
        event_type = AuditType.QUERY

    # Create agent
    agent = AuditAgent(
        who=user or f"connection:{connection_id}",
        name=user,
        requestor=True,
    )

    # Create entities
    entities: list[AuditEntity] = []

    if resource_type and resource_id:
        entities.append(
            AuditEntity(
                what=f"{resource_type}/{resource_id}",
                type_code="2" if resource_type == "Patient" else "1",  # 2=Patient, 1=Person
                role_code="1",  # Patient
            )
        )
    elif resource_type:
        import base64

        entities.append(
            AuditEntity(
                what=resource_type,
                type_code="1",
                role_code="24",  # Query
                query=base64.b64encode(query.encode()).decode() if query else None,
            )
        )

    return AuditEvent(
        type=event_type,
        subtype=subtype,
        action=action,
        outcome=outcome,
        agent=agent,
        entity=entities,
        outcome_desc=outcome_desc,
    )

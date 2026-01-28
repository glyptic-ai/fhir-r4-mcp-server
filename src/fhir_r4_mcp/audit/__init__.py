"""FHIR R4 Audit Event logging module for HIPAA-compliant access logging."""

from fhir_r4_mcp.audit.events import (
    AuditAction,
    AuditAgent,
    AuditEntity,
    AuditEvent,
    AuditOutcome,
    AuditSource,
    AuditSubtype,
    AuditType,
)
from fhir_r4_mcp.audit.logger import (
    AuditConfig,
    AuditLogger,
    audit_logger,
    audit_tool,
)

__all__ = [
    # Event classes
    "AuditEvent",
    "AuditAgent",
    "AuditSource",
    "AuditEntity",
    "AuditType",
    "AuditSubtype",
    "AuditAction",
    "AuditOutcome",
    # Logger
    "AuditLogger",
    "AuditConfig",
    "audit_logger",
    "audit_tool",
]

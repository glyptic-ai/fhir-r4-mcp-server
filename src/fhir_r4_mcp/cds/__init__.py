"""CDS Hooks support for clinical decision support integration."""

from fhir_r4_mcp.cds.hooks import (
    CDSCard,
    CDSHook,
    CDSHookRequest,
    CDSHookResponse,
    CDSLink,
    CDSSuggestion,
    HookType,
)
from fhir_r4_mcp.cds.service import (
    CDSService,
    CDSServiceDiscovery,
    cds_service,
)

__all__ = [
    # Hooks
    "HookType",
    "CDSHook",
    "CDSHookRequest",
    "CDSHookResponse",
    "CDSCard",
    "CDSSuggestion",
    "CDSLink",
    # Service
    "CDSService",
    "CDSServiceDiscovery",
    "cds_service",
]

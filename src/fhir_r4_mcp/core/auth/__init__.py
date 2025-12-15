"""Authentication providers for FHIR R4 MCP Server."""

from fhir_r4_mcp.core.auth.base import AuthProvider, AuthResult
from fhir_r4_mcp.core.auth.smart_backend import SMARTBackendAuth

__all__ = ["AuthProvider", "AuthResult", "SMARTBackendAuth"]

"""FHIR R4 MCP Server - AI-agnostic Model Context Protocol server for FHIR R4 EHR integration."""

__version__ = "0.1.0"
__author__ = "Glyptic AI"
__license__ = "Apache-2.0"

from fhir_r4_mcp.server import create_server

__all__ = ["create_server", "__version__"]

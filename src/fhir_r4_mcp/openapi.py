"""OpenAPI specification generator for FHIR R4 MCP Server.

This module generates OpenAPI 3.0 specifications from the MCP tools
defined in the server.
"""

import inspect
import json
import re
from pathlib import Path
from typing import Any, get_type_hints

from fhir_r4_mcp.utils.logging import get_logger

logger = get_logger(__name__)

# OpenAPI spec version
OPENAPI_VERSION = "3.0.3"

# Server info
SERVER_INFO = {
    "title": "FHIR R4 MCP Server API",
    "description": "AI-agnostic Model Context Protocol server for FHIR R4 EHR integration",
    "version": "0.1.0",
    "contact": {
        "name": "Glyptic AI",
        "email": "dev@glyptic.ai",
    },
    "license": {
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
}


def python_type_to_openapi(py_type: Any) -> dict[str, Any]:
    """Convert Python type hint to OpenAPI schema.

    Args:
        py_type: Python type hint

    Returns:
        OpenAPI schema object
    """
    # Handle None type
    if py_type is None or py_type is type(None):
        return {"type": "null"}

    # Get origin for generic types
    origin = getattr(py_type, "__origin__", None)

    # Handle Optional (Union with None)
    if origin is type(None):
        return {"type": "null"}

    # Handle Union types (including Optional)
    if origin is not None:
        args = getattr(py_type, "__args__", ())

        # List types
        if origin is list:
            if args:
                return {
                    "type": "array",
                    "items": python_type_to_openapi(args[0]),
                }
            return {"type": "array"}

        # Dict types
        if origin is dict:
            if len(args) >= 2:
                return {
                    "type": "object",
                    "additionalProperties": python_type_to_openapi(args[1]),
                }
            return {"type": "object"}

        # Union types (handle Optional)
        import typing

        if origin is typing.Union:
            # Check if it's Optional (Union with None)
            non_none_args = [a for a in args if a is not type(None)]
            if len(non_none_args) == 1:
                schema = python_type_to_openapi(non_none_args[0])
                schema["nullable"] = True
                return schema
            # Multiple non-None types - use oneOf
            return {
                "oneOf": [python_type_to_openapi(a) for a in non_none_args],
            }

    # Handle basic types
    if py_type is str:
        return {"type": "string"}
    if py_type is int:
        return {"type": "integer"}
    if py_type is float:
        return {"type": "number"}
    if py_type is bool:
        return {"type": "boolean"}

    # Handle dict without type hints
    if py_type is dict:
        return {"type": "object"}

    # Handle list without type hints
    if py_type is list:
        return {"type": "array"}

    # Handle Any
    if py_type is Any:
        return {}

    # Default to object
    return {"type": "object"}


def parse_docstring(docstring: str | None) -> dict[str, Any]:
    """Parse a function docstring to extract description and parameters.

    Args:
        docstring: Function docstring

    Returns:
        Dict with description, args, and returns info
    """
    if not docstring:
        return {"description": "", "args": {}, "returns": ""}

    lines = docstring.strip().split("\n")
    result: dict[str, Any] = {
        "description": "",
        "args": {},
        "returns": "",
    }

    # Parse description (first lines before Args/Returns)
    description_lines = []
    current_section = "description"
    current_arg = None

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("Args:"):
            current_section = "args"
            continue
        elif stripped.startswith("Returns:"):
            current_section = "returns"
            continue
        elif stripped.startswith("Raises:"):
            current_section = "raises"
            continue
        elif stripped.startswith("Example:"):
            current_section = "example"
            continue

        if current_section == "description":
            description_lines.append(stripped)

        elif current_section == "args":
            # Parse arg: description format
            if ":" in stripped and not stripped.startswith(" "):
                parts = stripped.split(":", 1)
                arg_name = parts[0].strip()
                arg_desc = parts[1].strip() if len(parts) > 1 else ""
                result["args"][arg_name] = arg_desc
                current_arg = arg_name
            elif current_arg and stripped:
                # Continuation of previous arg description
                result["args"][current_arg] += " " + stripped

        elif current_section == "returns":
            if result["returns"]:
                result["returns"] += " "
            result["returns"] += stripped

    result["description"] = " ".join(description_lines).strip()

    return result


def generate_tool_schema(func: Any, tool_name: str) -> dict[str, Any]:
    """Generate OpenAPI schema for a single tool function.

    Args:
        func: The tool function
        tool_name: Name of the tool

    Returns:
        OpenAPI operation schema
    """
    # Get type hints
    try:
        hints = get_type_hints(func)
    except Exception:
        hints = {}

    # Get signature
    sig = inspect.signature(func)

    # Parse docstring
    doc_info = parse_docstring(func.__doc__)

    # Build parameters schema
    properties: dict[str, Any] = {}
    required: list[str] = []

    for param_name, param in sig.parameters.items():
        if param_name in ("self", "cls"):
            continue

        param_schema: dict[str, Any] = {}

        # Get type from hints
        if param_name in hints:
            param_schema = python_type_to_openapi(hints[param_name])

        # Get description from docstring
        if param_name in doc_info["args"]:
            param_schema["description"] = doc_info["args"][param_name]

        # Check if required (no default value)
        if param.default is inspect.Parameter.empty:
            required.append(param_name)
        else:
            # Add default value
            if param.default is not None:
                param_schema["default"] = param.default

        properties[param_name] = param_schema

    # Build response schema
    return_schema: dict[str, Any] = {"type": "object"}
    if "return" in hints:
        return_schema = python_type_to_openapi(hints["return"])

    # Build operation
    operation: dict[str, Any] = {
        "operationId": tool_name,
        "summary": doc_info["description"].split(".")[0] if doc_info["description"] else tool_name,
        "description": doc_info["description"],
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": properties,
                        "required": required if required else None,
                    }
                }
            },
        },
        "responses": {
            "200": {
                "description": doc_info["returns"] or "Successful response",
                "content": {
                    "application/json": {
                        "schema": return_schema,
                    }
                },
            },
            "400": {
                "description": "Validation error",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/OperationOutcome"},
                    }
                },
            },
            "401": {
                "description": "Authentication error",
            },
            "404": {
                "description": "Resource not found",
            },
            "500": {
                "description": "Server error",
            },
        },
    }

    # Remove None values from required
    if operation["requestBody"]["content"]["application/json"]["schema"]["required"] is None:
        del operation["requestBody"]["content"]["application/json"]["schema"]["required"]

    return operation


def generate_openapi_spec() -> dict[str, Any]:
    """Generate OpenAPI 3.0 specification from MCP tools.

    Returns:
        Complete OpenAPI specification dictionary
    """
    from fhir_r4_mcp.server import create_server

    # Create server to get tool definitions
    mcp = create_server()

    # Start building spec
    spec: dict[str, Any] = {
        "openapi": OPENAPI_VERSION,
        "info": SERVER_INFO,
        "servers": [
            {
                "url": "http://localhost:8080",
                "description": "Local development server",
            }
        ],
        "paths": {},
        "components": {
            "schemas": {
                "OperationOutcome": {
                    "type": "object",
                    "properties": {
                        "resourceType": {
                            "type": "string",
                            "enum": ["OperationOutcome"],
                        },
                        "issue": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "severity": {
                                        "type": "string",
                                        "enum": ["fatal", "error", "warning", "information"],
                                    },
                                    "code": {"type": "string"},
                                    "diagnostics": {"type": "string"},
                                },
                            },
                        },
                    },
                },
                "Bundle": {
                    "type": "object",
                    "properties": {
                        "resourceType": {
                            "type": "string",
                            "enum": ["Bundle"],
                        },
                        "type": {"type": "string"},
                        "total": {"type": "integer"},
                        "entry": {
                            "type": "array",
                            "items": {"type": "object"},
                        },
                    },
                },
                "FHIRResource": {
                    "type": "object",
                    "properties": {
                        "resourceType": {"type": "string"},
                        "id": {"type": "string"},
                    },
                },
            },
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                },
                "apiKey": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-API-Key",
                },
            },
        },
        "security": [
            {"bearerAuth": []},
            {"apiKey": []},
        ],
        "tags": [
            {"name": "Connection", "description": "FHIR server connection management"},
            {"name": "Patient", "description": "Patient-related operations"},
            {"name": "Resource", "description": "Generic FHIR resource operations"},
            {"name": "Clinical", "description": "Clinical data operations"},
            {"name": "Bulk", "description": "Bulk data export operations"},
            {"name": "Group", "description": "Group management operations"},
            {"name": "Metadata", "description": "Server metadata and capabilities"},
            {"name": "Transaction", "description": "Transaction and batch operations"},
            {"name": "History", "description": "Resource history operations"},
            {"name": "Validation", "description": "Resource validation operations"},
            {"name": "Terminology", "description": "Terminology service operations"},
            {"name": "Subscription", "description": "Subscription management"},
            {"name": "CDS", "description": "Clinical decision support"},
        ],
    }

    # Get tools from MCP server
    # The FastMCP stores tools in _tool_manager
    if hasattr(mcp, "_tool_manager") and hasattr(mcp._tool_manager, "_tools"):
        tools = mcp._tool_manager._tools
    else:
        # Fallback - try to inspect registered tools
        logger.warning("Could not access MCP tools directly")
        tools = {}

    # Generate paths for each tool
    for tool_name, tool in tools.items():
        # Get the function
        func = tool.fn if hasattr(tool, "fn") else tool

        # Generate operation schema
        operation = generate_tool_schema(func, tool_name)

        # Determine tag based on tool name
        tag = "Resource"  # Default
        if "connect" in tool_name.lower():
            tag = "Connection"
        elif "patient" in tool_name.lower():
            tag = "Patient"
        elif "bulk" in tool_name.lower() or "export" in tool_name.lower():
            tag = "Bulk"
        elif "group" in tool_name.lower():
            tag = "Group"
        elif "capability" in tool_name.lower() or "supported" in tool_name.lower():
            tag = "Metadata"
        elif "transaction" in tool_name.lower():
            tag = "Transaction"
        elif "history" in tool_name.lower() or "vread" in tool_name.lower():
            tag = "History"
        elif "clinical" in tool_name.lower() or "document" in tool_name.lower():
            tag = "Clinical"
        elif "validate" in tool_name.lower():
            tag = "Validation"
        elif "translate" in tool_name.lower():
            tag = "Terminology"
        elif "subscription" in tool_name.lower():
            tag = "Subscription"
        elif "cds" in tool_name.lower():
            tag = "CDS"
        elif "match" in tool_name.lower():
            tag = "Patient"

        operation["tags"] = [tag]

        # Add to paths
        path = f"/tools/{tool_name}"
        spec["paths"][path] = {"post": operation}

    logger.info(f"Generated OpenAPI spec with {len(spec['paths'])} endpoints")

    return spec


def export_openapi(output_path: str, format: str = "json") -> None:
    """Export OpenAPI specification to a file.

    Args:
        output_path: Path to output file
        format: Output format (json or yaml)
    """
    spec = generate_openapi_spec()

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if format == "yaml":
        import yaml

        with open(path, "w") as f:
            yaml.dump(spec, f, default_flow_style=False, sort_keys=False)
    else:
        with open(path, "w") as f:
            json.dump(spec, f, indent=2)

    logger.info(f"Exported OpenAPI spec to {path}")


def main() -> None:
    """CLI entry point for OpenAPI generation."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate OpenAPI specification")
    parser.add_argument(
        "--output", "-o",
        default="openapi.json",
        help="Output file path (default: openapi.json)",
    )
    parser.add_argument(
        "--format", "-f",
        choices=["json", "yaml"],
        default="json",
        help="Output format (default: json)",
    )

    args = parser.parse_args()

    export_openapi(args.output, args.format)
    print(f"OpenAPI specification exported to {args.output}")  # noqa: T201


if __name__ == "__main__":
    main()

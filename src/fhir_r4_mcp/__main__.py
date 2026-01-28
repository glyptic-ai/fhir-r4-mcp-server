"""Entry point for running the FHIR R4 MCP Server."""

import argparse
import sys

from fhir_r4_mcp.server import create_server


def main() -> None:
    """Run the FHIR R4 MCP Server or execute CLI commands."""
    parser = argparse.ArgumentParser(
        description="FHIR R4 MCP Server - AI-agnostic Model Context Protocol server for FHIR R4 EHR integration"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Serve command (default)
    serve_parser = subparsers.add_parser("serve", help="Run the MCP server")

    # OpenAPI command
    openapi_parser = subparsers.add_parser("openapi", help="Generate OpenAPI specification")
    openapi_parser.add_argument(
        "--output", "-o",
        default="openapi.json",
        help="Output file path (default: openapi.json)",
    )
    openapi_parser.add_argument(
        "--format", "-f",
        choices=["json", "yaml"],
        default="json",
        help="Output format (default: json)",
    )

    args = parser.parse_args()

    if args.command == "openapi":
        from fhir_r4_mcp.openapi import export_openapi
        export_openapi(args.output, args.format)
        print(f"OpenAPI specification exported to {args.output}")  # noqa: T201
    else:
        # Default: run the server
        server = create_server()
        server.run()


if __name__ == "__main__":
    main()

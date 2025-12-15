"""Entry point for running the FHIR R4 MCP Server."""

import asyncio
import sys

from fhir_r4_mcp.server import create_server


def main() -> None:
    """Run the FHIR R4 MCP Server."""
    server = create_server()
    server.run()


if __name__ == "__main__":
    main()

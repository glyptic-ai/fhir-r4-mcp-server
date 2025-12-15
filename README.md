# FHIR R4 MCP Server

AI-agnostic Model Context Protocol (MCP) server for FHIR R4 EHR integration.

## Overview

This open-source MCP server provides a standardized interface for AI systems to interact with FHIR R4-compliant Electronic Health Record (EHR) systems. It supports NextGen, Epic, Cerner, and any standards-compliant FHIR R4 server.

### Key Features

- **AI-Agnostic**: Works with Claude, GPT, open-source LLMs, or any MCP-compliant client
- **EHR-Agnostic**: Configurable for any FHIR R4-compliant server
- **20 MCP Tools**: Complete coverage for patient data, clinical notes, and bulk export
- **Stateless Design**: Token refresh handled per-request
- **SMART Backend Services**: Secure authentication using JWT/JWKS

## Quick Start

### Installation

```bash
# Using pip
pip install fhir-r4-mcp-server

# Using uv (recommended)
uv add fhir-r4-mcp-server
```

### Claude Desktop Configuration

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "fhir-r4": {
      "command": "python",
      "args": ["-m", "fhir_r4_mcp"],
      "env": {
        "FHIR_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### Docker

```bash
# Build and run
docker compose -p fhir-r4-mcp up -d

# View logs
docker compose -p fhir-r4-mcp logs -f

# Stop
docker compose -p fhir-r4-mcp down
```

## Available Tools

### Connection Management
| Tool | Description |
|------|-------------|
| `fhir_connect` | Register and authenticate with a FHIR server |
| `fhir_disconnect` | Remove a registered connection |
| `fhir_list_connections` | List all active connections |

### Patient Operations
| Tool | Description |
|------|-------------|
| `fhir_patient_search` | Search patients by name, DOB, MRN |
| `fhir_patient_read` | Get single patient by ID |
| `fhir_patient_everything` | Get all data for a patient |

### Clinical Queries
| Tool | Description |
|------|-------------|
| `fhir_query` | Generic FHIR resource query |
| `fhir_resource_read` | Read specific resource by ID |

### Clinical Notes
| Tool | Description |
|------|-------------|
| `fhir_clinical_notes` | Retrieve clinical notes by type |
| `fhir_document_content` | Get document content |

### Bulk Data Export
| Tool | Description |
|------|-------------|
| `fhir_bulk_export_start` | Start bulk export job |
| `fhir_bulk_export_status` | Check export status |
| `fhir_bulk_export_download` | Download export files |
| `fhir_bulk_export_cancel` | Cancel export job |

### Group Management
| Tool | Description |
|------|-------------|
| `fhir_group_create` | Create patient group |
| `fhir_group_list` | List groups |
| `fhir_group_members` | Get group members |
| `fhir_group_update` | Update group membership |

### Metadata
| Tool | Description |
|------|-------------|
| `fhir_capability_statement` | Get server capabilities |
| `fhir_supported_resources` | List supported resources |

## Authentication

### SMART Backend Services (Recommended)

```python
# Example connection using SMART Backend Services
await fhir_connect(
    connection_id="nextgen_prod",
    base_url="https://fhir.example.com/r4",
    auth_type="smart_backend",
    client_id="your-client-id",
    private_key_pem="/path/to/private_key.pem",
    vendor="nextgen"
)
```

### Supported Auth Types
- `smart_backend` - SMART Backend Services (JWT/JWKS)
- `oauth2` - OAuth2 Client Credentials
- `basic` - Basic Authentication
- `api_key` - API Key Authentication

## Supported EHR Systems

| Vendor | Status | Notes |
|--------|--------|-------|
| NextGen | Primary | Full bulk export support |
| Epic | Planned | Coming soon |
| Cerner | Planned | Coming soon |
| Generic | Supported | Any FHIR R4 server |

## Development

```bash
# Clone repository
git clone https://github.com/glyptic-ai/fhir-r4-mcp-server.git
cd fhir-r4-mcp-server

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/unit/

# Lint
ruff check src/
```

## License

Apache 2.0 - See [LICENSE](LICENSE) for details.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Support

- Issues: [GitHub Issues](https://github.com/glyptic-ai/fhir-r4-mcp-server/issues)
- Discussions: [GitHub Discussions](https://github.com/glyptic-ai/fhir-r4-mcp-server/discussions)

# Contributing to FHIR R4 MCP Server

Thank you for your interest in contributing to the FHIR R4 MCP Server! This document provides guidelines for contributing to the project.

## Code of Conduct

Please be respectful and constructive in all interactions. We welcome contributors of all experience levels.

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Git
- (Optional) Docker for container-based development

### Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/fhir-r4-mcp-server.git
   cd fhir-r4-mcp-server
   ```

3. Install dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

4. Run tests to verify setup:
   ```bash
   pytest tests/unit/
   ```

## Development Guidelines

### Code Style

- Follow PEP 8 guidelines
- Use type hints for all function signatures
- Maximum line length: 100 characters
- Use Ruff for linting: `ruff check src/`
- Use Black for formatting (via Ruff)

### Project Structure

```
src/fhir_r4_mcp/
├── core/           # Core components (client, auth, connections)
├── tools/          # MCP tool implementations
├── vendors/        # EHR vendor profiles
└── utils/          # Utilities (errors, logging)
```

### Adding New Tools

1. Define the tool in `src/fhir_r4_mcp/server.py`
2. Use the `@mcp.tool()` decorator
3. Follow the existing tool patterns for:
   - Input validation
   - Error handling
   - Response formatting
4. Add unit tests in `tests/unit/`

### Adding Vendor Profiles

1. Create a new file in `src/fhir_r4_mcp/vendors/`
2. Inherit from `VendorProfile`
3. Implement required methods for quirks and bulk config
4. Add vendor config in `config/vendors/`
5. Update the vendor registry in `vendors/__init__.py`

## Testing

### Unit Tests
```bash
# Run all unit tests
pytest tests/unit/

# Run with coverage
pytest tests/unit/ --cov=fhir_r4_mcp
```

### Integration Tests
Integration tests require a real FHIR server. Set environment variables:
```bash
export FHIR_TEST_BASE_URL=https://sandbox.example.com/r4
export FHIR_TEST_CLIENT_ID=your-client-id
export FHIR_TEST_PRIVATE_KEY_PATH=/path/to/key.pem

pytest tests/integration/
```

## Pull Request Process

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes with clear, atomic commits

3. Ensure all tests pass:
   ```bash
   pytest tests/unit/
   ruff check src/
   ```

4. Push to your fork and create a Pull Request

5. Fill out the PR template with:
   - Description of changes
   - Related issues
   - Testing performed
   - Breaking changes (if any)

### PR Requirements

- All tests must pass
- Code must be linted (Ruff)
- Type hints required for new code
- Documentation updated if needed
- No secrets or credentials committed

## Reporting Issues

### Bug Reports

Please include:
- Python version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Error messages/stack traces

### Feature Requests

Please include:
- Use case description
- Proposed solution (if any)
- Alternatives considered

## Security

**Do not report security vulnerabilities through public GitHub issues.**

Please email security concerns to: security@glyptic.ai

## License

By contributing, you agree that your contributions will be licensed under the Apache 2.0 License.

## Questions?

- Open a GitHub Discussion for general questions
- Tag maintainers in issues for specific questions

Thank you for contributing!

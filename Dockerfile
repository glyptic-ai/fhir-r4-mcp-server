# FHIR R4 MCP Server Dockerfile
# Multi-stage build for optimal image size

# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir build && \
    pip wheel --no-cache-dir --wheel-dir /app/wheels .

# Runtime stage
FROM python:3.11-slim as runtime

WORKDIR /app

# Create non-root user for security
RUN groupadd -r fhirmcp && useradd -r -g fhirmcp fhirmcp

# Copy wheels from builder and install
COPY --from=builder /app/wheels /app/wheels
RUN pip install --no-cache-dir /app/wheels/* && \
    rm -rf /app/wheels

# Copy application code
COPY src/ ./src/
COPY config/ ./config/

# Set ownership
RUN chown -R fhirmcp:fhirmcp /app

# Switch to non-root user
USER fhirmcp

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FHIR_LOG_LEVEL=INFO

# Expose port for HTTP transport (if used)
EXPOSE 8013

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import fhir_r4_mcp; print('healthy')" || exit 1

# Default command - stdio transport for MCP
CMD ["python", "-m", "fhir_r4_mcp"]

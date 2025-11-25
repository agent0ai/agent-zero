# =============================================================================
# Qdrant MCP Server - Admin Tools Container
# =============================================================================
# Provides MCP (Model Context Protocol) interface for Qdrant administration
# Exposes collection management, search, and optimization tools
# =============================================================================

FROM python:3.11-slim

LABEL maintainer="Agent Zero Unity Project"
LABEL description="Qdrant Admin MCP Server for collection management and optimization"
LABEL version="1.0.0"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 mcpuser && \
    chown -R mcpuser:mcpuser /app

USER mcpuser

# Environment defaults
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MCP_SERVER_PORT=8080 \
    MCP_LOG_LEVEL=info \
    QDRANT_URL=http://qdrant-unity:6333

# Expose MCP port
EXPOSE 8080

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -sf http://localhost:8080/health || exit 1

# Run the MCP server
CMD ["python", "server.py"]

# ServiceNow MCP Server Docker Image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create non-root user
RUN groupadd -r mcpuser && useradd -r -g mcpuser mcpuser

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories and set permissions
RUN mkdir -p /app/logs /app/cache && \
    chown -R mcpuser:mcpuser /app

# Switch to non-root user
USER mcpuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from servicenow_mcp.client_manager import client_manager; client_manager.health_check()" || exit 1

# Expose port (if running as HTTP server)
EXPOSE 8000

# Default command
CMD ["python", "mcp_adapter.py"]

# Labels for metadata
LABEL maintainer="ServiceNow MCP Contributors" \
      version="0.8.0" \
      description="ServiceNow Model Context Protocol Server" \
      org.opencontainers.image.source="https://github.com/yourusername/servicenow-mcp" \
      org.opencontainers.image.documentation="https://github.com/yourusername/servicenow-mcp/blob/main/README.md" \
      org.opencontainers.image.licenses="MIT"
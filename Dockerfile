# =============================================================================
# Mnemosyne - Your Digital Twin
# Multi-stage Dockerfile for production deployment
# =============================================================================

# Stage 1: Base image with Python and system dependencies
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash mnemosyne
WORKDIR /home/mnemosyne/app

# =============================================================================
# Stage 2: Dependencies
# =============================================================================
FROM base as deps

# Copy only requirements first for better caching
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install build && \
    pip install -e ".[web]"

# =============================================================================
# Stage 3: Production image
# =============================================================================
FROM base as production

# Copy installed packages from deps stage
COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=mnemosyne:mnemosyne . .

# Install the package
RUN pip install -e . --no-deps

# Switch to non-root user
USER mnemosyne

# Create data directory
RUN mkdir -p /home/mnemosyne/.mnemosyne

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command: run web server
CMD ["mnemosyne", "web", "--host", "0.0.0.0", "--port", "8000"]

# =============================================================================
# Stage 4: Development image
# =============================================================================
FROM production as development

USER root

# Install development dependencies
RUN pip install -e ".[dev]"

# Switch back to non-root user
USER mnemosyne

# Development command with auto-reload
CMD ["mnemosyne", "web", "--host", "0.0.0.0", "--port", "8000", "--reload"]

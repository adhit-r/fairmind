# Multi-stage production-ready Dockerfile
FROM python:3.11-slim@sha256:b596083aa14d47c78a652138aa9b98607585499d7c7ec343ae378f6c5770822d as builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install Python dependencies
COPY requirements.txt pyproject.toml ./
RUN pip install --upgrade "pip==24.2" "setuptools==75.1.0" "wheel==0.44.0" && \
    pip install -r requirements.txt && \
    pip install python-json-logger psutil

# Production stage
FROM python:3.11-slim@sha256:b596083aa14d47c78a652138aa9b98607585499d7c7ec343ae378f6c5770822d as production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    NODE_ENV=production

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN groupadd -r fairmind && useradd -r -g fairmind fairmind

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=fairmind:fairmind . .

# Create required directories
RUN mkdir -p uploads datasets models logs && \
    chown -R fairmind:fairmind /app

# Switch to non-root user
USER fairmind

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/live || exit 1

# Expose port
EXPOSE 8000

# Start command
CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

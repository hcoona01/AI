# ==============================================================================
# Production Dockerfile for University Faculty Workload Balancing Backend
# Base Image: Python 3.11 slim (Debian Bookworm) - Minimal attack surface, CPU-only
# Single-Worker: GitHub Gist storage assumes a single writer to prevent concurrency races.
# Memory Budget: Strictly operates within <= 512 MB RAM.
#
# MEMORY OPTIMIZATION NOTE:
# Setting FORECAST_MODE=precomputed bypasses loading the LightGBM booster model
# into runtime memory, reducing resident memory (RSS) by ~80-120 MB while serving
# precomputed demand quantiles (P10/P50/P90) from the scenario configurations.
# ==============================================================================

FROM python:3.11-slim AS runtime

# Prevent Python from writing .pyc files and enable unbuffered standard I/O
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app:/app/backend:/app/ml \
    PORT=8000 \
    ENVIRONMENT=production \
    STORE_BACKEND=gist \
    OTP_DEV_MODE=false \
    FORECAST_MODE=precomputed

WORKDIR /app

# Install minimal system utilities for TLS and container healthchecks
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install ONLY runtime dependencies (no dev tools like pytest, playwright, black, ruff)
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy ML package, application code, and seed data
COPY ml /app/ml
COPY backend /app/backend
COPY data /app/data

# Create and switch to non-privileged user for production security hardening
RUN useradd -u 1001 -m appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Container healthcheck monitoring endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Launch with exactly 1 worker:
# 1. GitHub Gist storage requires a single writer (optimistic concurrency without distributed locks).
# 2. Guarantees process memory stays comfortably inside the 512 MB RAM envelope.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --log-level info"]


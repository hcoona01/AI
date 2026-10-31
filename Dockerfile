# Root Dockerfile pointing to production runtime configuration
# See backend/Dockerfile for documentation on memory budget & single-worker design

FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app:/app/backend:/app/ml \
    PORT=8000 \
    ENVIRONMENT=production \
    STORE_BACKEND=gist \
    OTP_DEV_MODE=false \
    FORECAST_MODE=precomputed

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/backend/requirements.txt

COPY ml /app/ml
COPY backend /app/backend
COPY data /app/data

RUN useradd -u 1001 -m appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --log-level info"]


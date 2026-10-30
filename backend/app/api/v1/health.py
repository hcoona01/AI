from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=dict[str, Any])
async def get_health() -> dict[str, Any]:
    """Health check endpoint returning system status and configuration mode."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "store_backend": settings.STORE_BACKEND,
        "forecast_mode": settings.FORECAST_MODE,
        "timestamp": datetime.now(UTC).isoformat(),
    }

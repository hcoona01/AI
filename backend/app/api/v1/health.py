from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(tags=["Health"])


def _get_process_memory_mb() -> float | None:
    """Safely measure resident set size without heavy external dependencies."""
    try:
        import resource  # Linux / Unix / macOS
        return round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0, 2)
    except Exception:
        pass
    try:
        import tracemalloc
        if tracemalloc.is_tracing():
            current, _ = tracemalloc.get_traced_memory()
            return round(current / (1024.0 * 1024.0), 2)
    except Exception:
        pass
    return None


@router.get("/health", response_model=dict[str, Any])
async def get_health() -> dict[str, Any]:
    """Health check endpoint returning system status, compute budget headroom, and configuration mode."""
    mem_mb = _get_process_memory_mb()
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "store_backend": settings.STORE_BACKEND,
        "forecast_mode": settings.FORECAST_MODE,
        "memory_budget_mb": 512,
        "memory_observed_mb": mem_mb,
        "timestamp": datetime.now(UTC).isoformat(),
    }

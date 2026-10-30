"""Course demand forecasting endpoints (P10/P50/P90 projections)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field

from app.core.security import require_admin, require_authenticated
from app.schemas.forecast import ForecastRecord, ForecastRunResponse
from app.schemas.user import User
from app.services.forecast_service import ForecastService

router = APIRouter(prefix="/forecast", tags=["Forecast"])


def get_forecast_service() -> ForecastService:
    return ForecastService()


class ForecastRunRequest(BaseModel):
    term: str | None = Field(
        default=None, description="Optional target academic term (e.g. 'Fall 2026')"
    )


@router.post(
    "/run",
    response_model=ForecastRunResponse,
    status_code=status.HTTP_200_OK,
)
async def run_forecast(
    admin_user: Annotated[User, Depends(require_admin)],
    service: Annotated[ForecastService, Depends(get_forecast_service)],
    body: ForecastRunRequest | None = None,
) -> ForecastRunResponse:
    """Admin-only: Run demand forecast inference using saved artifacts.

    Does NOT train models. Returns 503 if artifacts are missing.
    Updates section records with predicted quantiles (P10, P50, P90).
    """
    term = body.term if body else None
    return await service.run_forecast(term=term, actor_id=admin_user.id)


@router.get("", response_model=list[ForecastRecord])
async def get_forecasts(
    _: Annotated[User, Depends(require_authenticated)],
    service: Annotated[ForecastService, Depends(get_forecast_service)],
    term: Annotated[
        str | None,
        Query(description="Filter forecasts by term (e.g. 'Fall 2026')"),
    ] = None,
) -> list[ForecastRecord]:
    """Retrieve demand forecasts, optionally filtered by academic term."""
    return await service.get_forecasts(term=term)

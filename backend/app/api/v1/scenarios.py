"""Scenarios API router for loading evaluation fixtures into active persistence."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends

from app.core.security import require_admin
from app.schemas.user import User
from app.services.scenario_service import ScenarioService

router = APIRouter(prefix="/scenarios", tags=["Scenarios"])


def get_scenario_service() -> ScenarioService:
    return ScenarioService()


@router.post("/load/{name}", response_model=dict[str, Any])
async def load_scenario_fixture(
    name: str,
    admin_user: Annotated[User, Depends(require_admin)],
    service: Annotated[ScenarioService, Depends(get_scenario_service)],
) -> dict[str, Any]:
    """Admin-only: Load an evaluation fixture from /data/fixtures into store and record audit log."""
    return await service.load_scenario(scenario_name=name, actor_id=admin_user.id)

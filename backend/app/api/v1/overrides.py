"""Administrative override inspection endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.errors import NotFoundError
from app.core.security import require_admin
from app.repositories import get_override_repository
from app.repositories.base import Repository
from app.schemas.override import Override
from app.schemas.user import User

router = APIRouter(prefix="/overrides", tags=["Overrides"])


@router.get("", response_model=list[Override])
async def list_overrides(
    _: Annotated[User, Depends(require_admin)],
    repo: Annotated[Repository[Override], Depends(get_override_repository)],
    assignment_id: Annotated[
        str | None, Query(description="Filter by target assignment ID")
    ] = None,
) -> list[Override]:
    """Admin-only: Retrieve all manual override records with constraint evidence snapshots."""
    overrides = await repo.get_all()
    if assignment_id:
        return [o for o in overrides if o.assignment_id == assignment_id]
    return overrides


@router.get("/{override_id}", response_model=Override)
async def get_override(
    override_id: str,
    _: Annotated[User, Depends(require_admin)],
    repo: Annotated[Repository[Override], Depends(get_override_repository)],
) -> Override:
    """Admin-only: Retrieve a single override record by its ID."""
    override = await repo.get(override_id)
    if not override:
        raise NotFoundError(f"Override '{override_id}' not found")
    return override

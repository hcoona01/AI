"""Authenticated user profile endpoint."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.security import require_authenticated
from app.schemas.user import User

router = APIRouter(prefix="/me", tags=["Me"])


@router.get("", response_model=User)
async def get_my_profile(
    current_user: Annotated[User, Depends(require_authenticated)],
) -> User:
    """Retrieve profile of currently authenticated user (derived from active session)."""
    return current_user

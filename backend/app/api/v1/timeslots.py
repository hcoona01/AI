"""TimeSlots API router for weekly academic scheduling grid."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.security import require_admin, require_authenticated
from app.schemas.timeslot import TimeSlot
from app.schemas.user import User
from app.services.timeslot_service import TimeSlotService

router = APIRouter(prefix="/timeslots", tags=["TimeSlots"])


def get_timeslot_service() -> TimeSlotService:
    return TimeSlotService()


@router.get("", response_model=list[TimeSlot])
async def list_timeslots(
    _: Annotated[User, Depends(require_authenticated)],
    service: Annotated[TimeSlotService, Depends(get_timeslot_service)],
) -> list[TimeSlot]:
    """Retrieve all weekly timeslots (shared reference data)."""
    return await service.get_all()


@router.get("/{slot_id}", response_model=TimeSlot)
async def get_timeslot(
    slot_id: str,
    _: Annotated[User, Depends(require_authenticated)],
    service: Annotated[TimeSlotService, Depends(get_timeslot_service)],
) -> TimeSlot:
    """Retrieve timeslot definition by ID."""
    return await service.get_by_id(slot_id=slot_id)


@router.post("", response_model=TimeSlot, status_code=status.HTTP_201_CREATED)
async def create_timeslot(
    timeslot: TimeSlot,
    admin_user: Annotated[User, Depends(require_admin)],
    service: Annotated[TimeSlotService, Depends(get_timeslot_service)],
) -> TimeSlot:
    """Admin-only: Create a new timeslot in the scheduling grid and record an audit log."""
    return await service.create(timeslot=timeslot, actor_id=admin_user.id)


@router.put("/{slot_id}", response_model=TimeSlot)
async def update_timeslot(
    slot_id: str,
    timeslot: TimeSlot,
    admin_user: Annotated[User, Depends(require_admin)],
    service: Annotated[TimeSlotService, Depends(get_timeslot_service)],
) -> TimeSlot:
    """Admin-only: Update timeslot interval and record an audit log."""
    return await service.update(
        slot_id=slot_id, timeslot=timeslot, actor_id=admin_user.id
    )


@router.delete("/{slot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_timeslot(
    slot_id: str,
    admin_user: Annotated[User, Depends(require_admin)],
    service: Annotated[TimeSlotService, Depends(get_timeslot_service)],
) -> None:
    """Admin-only: Remove a timeslot from the scheduling grid and record an audit log."""
    await service.delete(slot_id=slot_id, actor_id=admin_user.id)

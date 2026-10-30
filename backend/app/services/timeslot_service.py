"""TimeSlot service managing academic scheduling grid."""

from __future__ import annotations

import logging

from app.core.errors import ConflictError, NotFoundError
from app.repositories import get_timeslot_repository
from app.repositories.base import Repository
from app.schemas.timeslot import TimeSlot
from app.services.audit_service import AuditService

logger = logging.getLogger("app.services.timeslot")


class TimeSlotService:
    """Service managing academic timeslot definitions."""

    def __init__(
        self,
        repository: Repository[TimeSlot] | None = None,
        audit_service: AuditService | None = None,
    ) -> None:
        self.repository = repository or get_timeslot_repository()
        self.audit_service = audit_service or AuditService()

    async def get_all(self) -> list[TimeSlot]:
        """Fetch all weekly timeslots."""
        return await self.repository.get_all()

    async def get_by_id(self, slot_id: str) -> TimeSlot:
        """Fetch a specific timeslot by ID."""
        slot = await self.repository.get(slot_id)
        if not slot:
            raise NotFoundError(f"TimeSlot '{slot_id}' not found")
        return slot

    async def create(self, timeslot: TimeSlot, actor_id: str) -> TimeSlot:
        """Register a new timeslot (Admin only) and record audit log."""
        existing = await self.repository.get(timeslot.id)
        if existing:
            raise ConflictError(f"TimeSlot with ID '{timeslot.id}' already exists")

        created = await self.repository.upsert(timeslot)
        await self.audit_service.log_event(
            actor_id=actor_id,
            action="TIMESLOT_CREATED",
            entity="timeslot",
            payload=timeslot.model_dump(mode="json"),
        )
        return created

    async def update(self, slot_id: str, timeslot: TimeSlot, actor_id: str) -> TimeSlot:
        """Update an existing timeslot (Admin only) and record audit log."""
        existing = await self.repository.get(slot_id)
        if not existing:
            raise NotFoundError(f"Cannot update non-existent timeslot '{slot_id}'")

        timeslot.id = slot_id
        updated = await self.repository.upsert(timeslot)
        await self.audit_service.log_event(
            actor_id=actor_id,
            action="TIMESLOT_UPDATED",
            entity="timeslot",
            payload={"id": slot_id, "updated": timeslot.model_dump(mode="json")},
        )
        return updated

    async def delete(self, slot_id: str, actor_id: str) -> bool:
        """Delete a timeslot (Admin only) and record audit log."""
        existing = await self.repository.get(slot_id)
        if not existing:
            raise NotFoundError(f"Cannot delete non-existent timeslot '{slot_id}'")

        success = await self.repository.delete(slot_id)
        if success:
            await self.audit_service.log_event(
                actor_id=actor_id,
                action="TIMESLOT_DELETED",
                entity="timeslot",
                payload={
                    "id": slot_id,
                    "day": existing.day.value,
                    "interval": f"{existing.start}-{existing.end}",
                },
            )
        return success

"""Section management service with administrative CRUD and audit trail logging."""

from __future__ import annotations

import logging

from app.core.errors import ConflictError, NotFoundError
from app.repositories import get_section_repository
from app.repositories.base import Repository
from app.schemas.section import Section
from app.services.audit_service import AuditService

logger = logging.getLogger("app.services.section")


class SectionService:
    """Service managing academic term course sections."""

    def __init__(
        self,
        repository: Repository[Section] | None = None,
        audit_service: AuditService | None = None,
    ) -> None:
        self.repository = repository or get_section_repository()
        self.audit_service = audit_service or AuditService()

    async def get_all(self, term: str | None = None) -> list[Section]:
        """Fetch all sections, optionally filtered by term."""
        sections = await self.repository.get_all()
        if term:
            sections = [s for s in sections if s.term.lower() == term.lower()]
        return sections

    async def get_by_id(self, section_id: str) -> Section:
        """Fetch a specific section by ID."""
        section = await self.repository.get(section_id)
        if not section:
            raise NotFoundError(f"Section '{section_id}' not found")
        return section

    async def create(self, section: Section, actor_id: str) -> Section:
        """Create a new course section (Admin only) and record audit log."""
        existing = await self.repository.get(section.id)
        if existing:
            raise ConflictError(f"Section with ID '{section.id}' already exists")

        created = await self.repository.upsert(section)
        await self.audit_service.log_event(
            actor_id=actor_id,
            action="SECTION_CREATED",
            entity="section",
            payload=section.model_dump(mode="json"),
        )
        return created

    async def update(self, section_id: str, section: Section, actor_id: str) -> Section:
        """Update an existing course section (Admin only) and record audit log."""
        existing = await self.repository.get(section_id)
        if not existing:
            raise NotFoundError(f"Cannot update non-existent section '{section_id}'")

        section.id = section_id
        updated = await self.repository.upsert(section)
        await self.audit_service.log_event(
            actor_id=actor_id,
            action="SECTION_UPDATED",
            entity="section",
            payload={"id": section_id, "updated": section.model_dump(mode="json")},
        )
        return updated

    async def delete(self, section_id: str, actor_id: str) -> bool:
        """Delete a section (Admin only) and record audit log."""
        existing = await self.repository.get(section_id)
        if not existing:
            raise NotFoundError(f"Cannot delete non-existent section '{section_id}'")

        success = await self.repository.delete(section_id)
        if success:
            await self.audit_service.log_event(
                actor_id=actor_id,
                action="SECTION_DELETED",
                entity="section",
                payload={
                    "id": section_id,
                    "course_id": existing.course_id,
                    "term": existing.term,
                },
            )
        return success

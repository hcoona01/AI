"""Faculty service orchestrating role-aware querying, CRUD operations, and audit logging."""

from __future__ import annotations

import logging

from app.core.errors import ConflictError, ForbiddenError, NotFoundError
from app.repositories import get_faculty_repository
from app.repositories.base import Repository
from app.schemas.common import UserRole
from app.schemas.faculty import Faculty
from app.schemas.user import User
from app.services.audit_service import AuditService

logger = logging.getLogger("app.services.faculty")


class FacultyService:
    """Business logic for faculty directory management with RBAC filtering."""

    def __init__(
        self,
        repository: Repository[Faculty] | None = None,
        audit_service: AuditService | None = None,
    ) -> None:
        self.repository = repository or get_faculty_repository()
        self.audit_service = audit_service or AuditService()

    async def get_all(self, current_user: User) -> list[Faculty]:
        """Fetch faculty records. Admins see all; Faculty see only their own record."""
        all_faculty = await self.repository.get_all()

        if current_user.role == UserRole.ADMIN:
            return all_faculty

        # Role-aware filter: Faculty see only their own profile
        if not current_user.faculty_id:
            logger.warning(f"Faculty user {current_user.id} has no linked faculty_id")
            return []

        return [f for f in all_faculty if f.id == current_user.faculty_id]

    async def get_by_id(self, faculty_id: str, current_user: User) -> Faculty:
        """Fetch single faculty record enforcing role-based privacy."""
        if (
            current_user.role == UserRole.FACULTY
            and current_user.faculty_id != faculty_id
        ):
            logger.warning(
                f"Unauthorized read: Faculty {current_user.id} attempted to access profile {faculty_id}"
            )
            raise ForbiddenError(
                "Faculty members are restricted to viewing their own profile only"
            )

        faculty = await self.repository.get(faculty_id)
        if not faculty:
            raise NotFoundError(f"Faculty record '{faculty_id}' not found")
        return faculty

    async def create(self, faculty: Faculty, actor_id: str) -> Faculty:
        """Create a new faculty profile (Admin only) and record audit log."""
        existing = await self.repository.get(faculty.id)
        if existing:
            raise ConflictError(f"Faculty with ID '{faculty.id}' already exists")

        created = await self.repository.upsert(faculty)
        await self.audit_service.log_event(
            actor_id=actor_id,
            action="FACULTY_CREATED",
            entity="faculty",
            payload=faculty.model_dump(mode="json"),
        )
        return created

    async def update(self, faculty_id: str, faculty: Faculty, actor_id: str) -> Faculty:
        """Update an existing faculty profile (Admin only) and record audit log."""
        existing = await self.repository.get(faculty_id)
        if not existing:
            raise NotFoundError(f"Cannot update non-existent faculty '{faculty_id}'")

        faculty.id = faculty_id
        updated = await self.repository.upsert(faculty)
        await self.audit_service.log_event(
            actor_id=actor_id,
            action="FACULTY_UPDATED",
            entity="faculty",
            payload={"id": faculty_id, "updated": faculty.model_dump(mode="json")},
        )
        return updated

    async def delete(self, faculty_id: str, actor_id: str) -> bool:
        """Delete a faculty profile (Admin only) and record audit log."""
        existing = await self.repository.get(faculty_id)
        if not existing:
            raise NotFoundError(f"Cannot delete non-existent faculty '{faculty_id}'")

        success = await self.repository.delete(faculty_id)
        if success:
            await self.audit_service.log_event(
                actor_id=actor_id,
                action="FACULTY_DELETED",
                entity="faculty",
                payload={"id": faculty_id, "name": existing.name},
            )
        return success

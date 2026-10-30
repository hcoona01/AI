"""Course management service with administrative CRUD and audit trail logging."""

from __future__ import annotations

import logging

from app.core.errors import ConflictError, NotFoundError
from app.repositories import get_course_repository
from app.repositories.base import Repository
from app.schemas.course import Course
from app.services.audit_service import AuditService

logger = logging.getLogger("app.services.course")


class CourseService:
    """Service managing academic course catalog."""

    def __init__(
        self,
        repository: Repository[Course] | None = None,
        audit_service: AuditService | None = None,
    ) -> None:
        self.repository = repository or get_course_repository()
        self.audit_service = audit_service or AuditService()

    async def get_all(self) -> list[Course]:
        """Fetch all courses (shared reference data accessible by all authenticated users)."""
        return await self.repository.get_all()

    async def get_by_id(self, course_id: str) -> Course:
        """Fetch a specific course by ID."""
        course = await self.repository.get(course_id)
        if not course:
            raise NotFoundError(f"Course '{course_id}' not found")
        return course

    async def create(self, course: Course, actor_id: str) -> Course:
        """Create a new course (Admin only) and record audit log."""
        existing = await self.repository.get(course.id)
        if existing:
            raise ConflictError(f"Course with ID '{course.id}' already exists")

        created = await self.repository.upsert(course)
        await self.audit_service.log_event(
            actor_id=actor_id,
            action="COURSE_CREATED",
            entity="course",
            payload=course.model_dump(mode="json"),
        )
        return created

    async def update(self, course_id: str, course: Course, actor_id: str) -> Course:
        """Update an existing course (Admin only) and record audit log."""
        existing = await self.repository.get(course_id)
        if not existing:
            raise NotFoundError(f"Cannot update non-existent course '{course_id}'")

        course.id = course_id
        updated = await self.repository.upsert(course)
        await self.audit_service.log_event(
            actor_id=actor_id,
            action="COURSE_UPDATED",
            entity="course",
            payload={"id": course_id, "updated": course.model_dump(mode="json")},
        )
        return updated

    async def delete(self, course_id: str, actor_id: str) -> bool:
        """Delete a course (Admin only) and record audit log."""
        existing = await self.repository.get(course_id)
        if not existing:
            raise NotFoundError(f"Cannot delete non-existent course '{course_id}'")

        success = await self.repository.delete(course_id)
        if success:
            await self.audit_service.log_event(
                actor_id=actor_id,
                action="COURSE_DELETED",
                entity="course",
                payload={"id": course_id, "code": existing.code},
            )
        return success

"""Faculty service orchestrating role-aware querying, CRUD operations, preferences, anonymized comparisons, and change requests."""

from __future__ import annotations

import logging
import statistics
import uuid
from datetime import UTC, datetime
from typing import Any

from app.core.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.repositories import (
    get_assignment_repository,
    get_change_request_repository,
    get_course_repository,
    get_faculty_repository,
    get_section_repository,
)
from app.repositories.base import Repository
from app.schemas.assignment import Assignment
from app.schemas.change_request import ChangeRequest
from app.schemas.common import UserRole
from app.schemas.course import Course
from app.schemas.faculty import Faculty
from app.schemas.section import Section
from app.schemas.user import User
from app.services.audit_service import AuditService

logger = logging.getLogger("app.services.faculty")


class FacultyService:
    """Business logic for faculty directory management with strict RBAC filtering."""

    def __init__(
        self,
        repository: Repository[Faculty] | None = None,
        audit_service: AuditService | None = None,
        assignment_repo: Repository[Assignment] | None = None,
        section_repo: Repository[Section] | None = None,
        course_repo: Repository[Course] | None = None,
        change_request_repo: Repository[ChangeRequest] | None = None,
    ) -> None:
        self.repository = repository or get_faculty_repository()
        self.audit_service = audit_service or AuditService()
        self.assignment_repo = assignment_repo or get_assignment_repository()
        self.section_repo = section_repo or get_section_repository()
        self.course_repo = course_repo or get_course_repository()
        self.change_request_repo = change_request_repo or get_change_request_repository()

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
                payload={"id": faculty_id},
            )
        return success

    async def update_preferences(
        self,
        faculty_id: str,
        unavailable_slots: list[str],
        leave_terms: list[str],
        preferred_course_ids: list[str],
        current_user: User,
    ) -> dict[str, Any]:
        """Update availability and teaching preferences (restricted to own ID)."""
        if (
            current_user.role == UserRole.FACULTY
            and current_user.faculty_id != faculty_id
        ):
            logger.warning(
                f"Unauthorized preferences update: User {current_user.id} tried to modify {faculty_id}"
            )
            raise ForbiddenError(
                "Faculty members are restricted to modifying their own preferences only"
            )

        existing = await self.repository.get(faculty_id)
        if not existing:
            raise NotFoundError(f"Faculty record '{faculty_id}' not found")

        updated = existing.model_copy(
            update={
                "unavailable_slots": unavailable_slots,
                "leave_terms": leave_terms,
                "preferred_course_ids": preferred_course_ids,
            }
        )
        await self.repository.upsert(updated)

        await self.audit_service.log_event(
            actor_id=current_user.id,
            action="FACULTY_PREFERENCES_UPDATE",
            entity="faculty",
            payload={
                "faculty_id": faculty_id,
                "unavailable_slots": unavailable_slots,
                "leave_terms": leave_terms,
                "preferred_course_ids": preferred_course_ids,
            },
        )

        return {
            "success": True,
            "faculty": updated.model_dump(mode="json"),
            "pending_optimization": True,
            "message": "Teaching preferences saved successfully. Status: Pending until the next optimizer execution.",
        }

    async def get_anonymized_load_comparison(
        self,
        faculty_id: str,
        term: str,
        current_user: User,
    ) -> dict[str, Any]:
        """Retrieve teaching load relative to department median with strictly anonymized peers."""
        if (
            current_user.role == UserRole.FACULTY
            and current_user.faculty_id != faculty_id
        ):
            logger.warning(
                f"Unauthorized load comparison query: User {current_user.id} tried to inspect {faculty_id}"
            )
            raise ForbiddenError(
                "Faculty members are restricted to viewing their own load comparison only"
            )

        all_faculty = await self.repository.get_all()
        target_faculty = next((f for f in all_faculty if f.id == faculty_id), None)
        if not target_faculty:
            raise NotFoundError(f"Faculty record '{faculty_id}' not found")

        all_assignments = await self.assignment_repo.get_all()
        all_sections = await self.section_repo.get_all()
        all_courses = await self.course_repo.get_all()

        section_map = {s.id: s for s in all_sections}
        course_map = {c.id: c for c in all_courses}

        # Filter assignments for specified term
        term_lower = term.lower()
        term_sections = {
            s.id: s for s in all_sections if s.term.lower() == term_lower
        }
        term_assignments = [
            a for a in all_assignments if a.section_id in term_sections
        ]

        # Calculate contact hours per faculty
        loads_by_faculty: dict[str, float] = {f.id: 0.0 for f in all_faculty}
        for a in term_assignments:
            sec = section_map.get(a.section_id)
            if sec:
                crs = course_map.get(sec.course_id)
                chours = crs.contact_hours if crs else 3.0
                loads_by_faculty[a.faculty_id] = (
                    loads_by_faculty.get(a.faculty_id, 0.0) + chours
                )

        all_loads = [round(loads_by_faculty.get(f.id, 0.0), 1) for f in all_faculty]
        median_load = round(statistics.median(all_loads) if all_loads else 0.0, 1)
        mean_load = round(statistics.mean(all_loads) if all_loads else 0.0, 1)

        my_load = round(loads_by_faculty.get(faculty_id, 0.0), 1)
        my_limit = target_faculty.max_weekly_load_hours

        # Anonymize peers: strictly NO names, NO emails, NO real faculty IDs
        anonymized_peers = []
        peer_counter = 1
        for f in all_faculty:
            rank_str = f.rank.value if hasattr(f.rank, "value") else str(f.rank)
            f_load = round(loads_by_faculty.get(f.id, 0.0), 1)
            f_ratio = round(f_load / max(f.max_weekly_load_hours, 1.0), 2)

            if f.id == faculty_id:
                anonymized_peers.append(
                    {
                        "peer_id": "you",
                        "label": "You (Your Load)",
                        "rank": rank_str,
                        "assigned_hours": f_load,
                        "max_limit": f.max_weekly_load_hours,
                        "load_ratio": f_ratio,
                        "is_current_user": True,
                    }
                )
            else:
                anonymized_peers.append(
                    {
                        "peer_id": f"peer-{peer_counter}",
                        "label": f"Peer {peer_counter} ({rank_str})",
                        "rank": rank_str,
                        "assigned_hours": f_load,
                        "max_limit": f.max_weekly_load_hours,
                        "load_ratio": f_ratio,
                        "is_current_user": False,
                    }
                )
                peer_counter += 1

        # Sort peers by assigned hours for clean distribution plotting
        anonymized_peers.sort(key=lambda x: x["assigned_hours"], reverse=True)

        return {
            "term": term,
            "faculty_id": faculty_id,
            "my_load": my_load,
            "my_max_limit": my_limit,
            "my_load_ratio": round(my_load / max(my_limit, 1.0), 2),
            "department_median_load": median_load,
            "department_mean_load": mean_load,
            "total_faculty_evaluated": len(all_faculty),
            "anonymized_peers": anonymized_peers,
        }

    async def create_change_request(
        self,
        assignment_id: str,
        comment: str,
        current_user: User,
    ) -> ChangeRequest:
        """Submit a change request / comment on an assigned section."""
        assignment = await self.assignment_repo.get(assignment_id)
        if not assignment:
            raise NotFoundError(f"Assignment '{assignment_id}' not found")

        # Ensure faculty user is actually assigned to this section
        if (
            current_user.role == UserRole.FACULTY
            and assignment.faculty_id != current_user.faculty_id
        ):
            raise ForbiddenError(
                "You can only submit change requests for sections assigned to you"
            )

        section = await self.section_repo.get(assignment.section_id)
        course = await self.course_repo.get(section.course_id) if section else None

        change_req = ChangeRequest(
            id=f"cr-{uuid.uuid4().hex[:8]}",
            assignment_id=assignment_id,
            faculty_id=assignment.faculty_id,
            section_id=assignment.section_id,
            course_code=course.code if course else "",
            comment=comment.strip(),
            status="pending",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        await self.change_request_repo.upsert(change_req)

        # Log event so administrative audit and notifications trigger
        await self.audit_service.log_event(
            actor_id=current_user.id,
            action="CHANGE_REQUEST_CREATED",
            entity="change_request",
            payload={
                "change_request_id": change_req.id,
                "assignment_id": assignment_id,
                "faculty_id": assignment.faculty_id,
                "section_id": assignment.section_id,
                "course_code": change_req.course_code,
                "comment": change_req.comment,
            },
        )

        return change_req

    async def get_change_requests(
        self,
        current_user: User,
        faculty_id: str | None = None,
    ) -> list[ChangeRequest]:
        """Fetch change requests. Faculty restricted strictly to their own."""
        all_requests = await self.change_request_repo.get_all()

        if current_user.role == UserRole.ADMIN:
            if faculty_id:
                return [r for r in all_requests if r.faculty_id == faculty_id]
            return all_requests

        # Faculty can only see their own requests
        target_fid = current_user.faculty_id or ""
        return [r for r in all_requests if r.faculty_id == target_fid]

    async def update_change_request_status(
        self,
        request_id: str,
        status: str,
        admin_response: str | None,
        actor_id: str,
    ) -> ChangeRequest:
        """Admin-only: Update change request status ('approved' or 'rejected')."""
        req = await self.change_request_repo.get(request_id)
        if not req:
            raise NotFoundError(f"Change request '{request_id}' not found")

        if status not in ("pending", "approved", "rejected"):
            raise ValidationError(f"Invalid status '{status}'")

        updated = req.model_copy(
            update={
                "status": status,
                "admin_response": admin_response,
                "updated_at": datetime.now(UTC),
            }
        )
        await self.change_request_repo.upsert(updated)

        await self.audit_service.log_event(
            actor_id=actor_id,
            action="CHANGE_REQUEST_STATUS_UPDATED",
            entity="change_request",
            payload={
                "change_request_id": request_id,
                "new_status": status,
                "admin_response": admin_response,
            },
        )
        return updated

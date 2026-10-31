"""Faculty API router with role-aware profile access, preferences, anonymized load comparisons, and change requests."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, ConfigDict, Field

from app.core.security import require_admin, require_authenticated
from app.schemas.change_request import ChangeRequest, ChangeRequestCreate
from app.schemas.faculty import Faculty
from app.schemas.user import User
from app.services.faculty_service import FacultyService

router = APIRouter(prefix="/faculty", tags=["Faculty"])


def get_faculty_service() -> FacultyService:
    return FacultyService()


class PreferencesUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    unavailable_slots: list[str] = Field(
        default_factory=list, description="Timeslot IDs faculty cannot teach"
    )
    leave_terms: list[str] = Field(
        default_factory=list, description="Academic terms on sabbatical/leave"
    )
    preferred_course_ids: list[str] = Field(
        default_factory=list, description="Preferred course IDs"
    )


class UpdateChangeRequestStatusPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    status: str = Field(..., pattern="^(pending|approved|rejected)$")
    admin_response: str | None = Field(default=None)


@router.get("", response_model=list[Faculty])
async def list_faculty(
    current_user: Annotated[User, Depends(require_authenticated)],
    service: Annotated[FacultyService, Depends(get_faculty_service)],
) -> list[Faculty]:
    """Retrieve faculty directory. Administrators see all profiles; Faculty members see only their own record."""
    return await service.get_all(current_user=current_user)


@router.get("/change-requests", response_model=list[ChangeRequest])
async def list_change_requests(
    current_user: Annotated[User, Depends(require_authenticated)],
    service: Annotated[FacultyService, Depends(get_faculty_service)],
    faculty_id: str | None = Query(default=None),
) -> list[ChangeRequest]:
    """List change requests. Faculty see only their own requests; Admins see all."""
    return await service.get_change_requests(
        current_user=current_user, faculty_id=faculty_id
    )


@router.post(
    "/change-requests",
    response_model=ChangeRequest,
    status_code=status.HTTP_201_CREATED,
)
async def create_change_request(
    payload: ChangeRequestCreate,
    current_user: Annotated[User, Depends(require_authenticated)],
    service: Annotated[FacultyService, Depends(get_faculty_service)],
) -> ChangeRequest:
    """Submit a change request or comment on an assigned section (restricted to assigned faculty)."""
    return await service.create_change_request(
        assignment_id=payload.assignment_id,
        comment=payload.comment,
        current_user=current_user,
    )


@router.put(
    "/change-requests/{request_id}/status",
    response_model=ChangeRequest,
)
async def update_change_request_status(
    request_id: str,
    payload: UpdateChangeRequestStatusPayload,
    admin_user: Annotated[User, Depends(require_admin)],
    service: Annotated[FacultyService, Depends(get_faculty_service)],
) -> ChangeRequest:
    """Admin-only: Review and approve/reject a faculty change request."""
    return await service.update_change_request_status(
        request_id=request_id,
        status=payload.status,
        admin_response=payload.admin_response,
        actor_id=admin_user.id,
    )


@router.get("/{faculty_id}", response_model=Faculty)
async def get_faculty(
    faculty_id: str,
    current_user: Annotated[User, Depends(require_authenticated)],
    service: Annotated[FacultyService, Depends(get_faculty_service)],
) -> Faculty:
    """Retrieve single faculty profile. Faculty members are strictly restricted to their own ID."""
    return await service.get_by_id(faculty_id=faculty_id, current_user=current_user)


@router.put("/{faculty_id}/preferences")
async def update_preferences(
    faculty_id: str,
    payload: PreferencesUpdateRequest,
    current_user: Annotated[User, Depends(require_authenticated)],
    service: Annotated[FacultyService, Depends(get_faculty_service)],
) -> dict[str, Any]:
    """Update teaching availability, leaves, and preferred courses (restricted to own ID)."""
    return await service.update_preferences(
        faculty_id=faculty_id,
        unavailable_slots=payload.unavailable_slots,
        leave_terms=payload.leave_terms,
        preferred_course_ids=payload.preferred_course_ids,
        current_user=current_user,
    )


@router.get("/{faculty_id}/load-comparison")
async def get_load_comparison(
    faculty_id: str,
    term: str = Query(..., description="Target academic term"),
    current_user: Annotated[User, Depends(require_authenticated)] = None,  # type: ignore[assignment]
    service: Annotated[FacultyService, Depends(get_faculty_service)] = None,  # type: ignore[assignment]
) -> dict[str, Any]:
    """Retrieve personal teaching load relative to department median with strictly anonymized peers."""
    return await service.get_anonymized_load_comparison(
        faculty_id=faculty_id,
        term=term,
        current_user=current_user,
    )


@router.post("", response_model=Faculty, status_code=status.HTTP_201_CREATED)
async def create_faculty(
    faculty: Faculty,
    admin_user: Annotated[User, Depends(require_admin)],
    service: Annotated[FacultyService, Depends(get_faculty_service)],
) -> Faculty:
    """Admin-only: Register a new faculty profile and record an audit log."""
    return await service.create(faculty=faculty, actor_id=admin_user.id)


@router.put("/{faculty_id}", response_model=Faculty)
async def update_faculty(
    faculty_id: str,
    faculty: Faculty,
    admin_user: Annotated[User, Depends(require_admin)],
    service: Annotated[FacultyService, Depends(get_faculty_service)],
) -> Faculty:
    """Admin-only: Update faculty profile parameters and record an audit log."""
    return await service.update(
        faculty_id=faculty_id, faculty=faculty, actor_id=admin_user.id
    )


@router.delete("/{faculty_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_faculty(
    faculty_id: str,
    admin_user: Annotated[User, Depends(require_admin)],
    service: Annotated[FacultyService, Depends(get_faculty_service)],
) -> None:
    """Admin-only: Delete a faculty profile and record an audit log."""
    await service.delete(faculty_id=faculty_id, actor_id=admin_user.id)

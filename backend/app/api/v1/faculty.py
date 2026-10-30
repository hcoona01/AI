"""Faculty API router with role-aware profile access and administrative CRUD."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.security import require_admin, require_authenticated
from app.schemas.faculty import Faculty
from app.schemas.user import User
from app.services.faculty_service import FacultyService

router = APIRouter(prefix="/faculty", tags=["Faculty"])


def get_faculty_service() -> FacultyService:
    return FacultyService()


@router.get("", response_model=list[Faculty])
async def list_faculty(
    current_user: Annotated[User, Depends(require_authenticated)],
    service: Annotated[FacultyService, Depends(get_faculty_service)],
) -> list[Faculty]:
    """Retrieve faculty directory. Administrators see all profiles; Faculty members see only their own record."""
    return await service.get_all(current_user=current_user)


@router.get("/{faculty_id}", response_model=Faculty)
async def get_faculty(
    faculty_id: str,
    current_user: Annotated[User, Depends(require_authenticated)],
    service: Annotated[FacultyService, Depends(get_faculty_service)],
) -> Faculty:
    """Retrieve single faculty profile. Faculty members are strictly restricted to their own ID."""
    return await service.get_by_id(faculty_id=faculty_id, current_user=current_user)


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

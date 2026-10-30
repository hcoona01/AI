"""Courses API router with shared reference reads and administrative CRUD."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.security import require_admin, require_authenticated
from app.schemas.course import Course
from app.schemas.user import User
from app.services.course_service import CourseService

router = APIRouter(prefix="/courses", tags=["Courses"])


def get_course_service() -> CourseService:
    return CourseService()


@router.get("", response_model=list[Course])
async def list_courses(
    _: Annotated[User, Depends(require_authenticated)],
    service: Annotated[CourseService, Depends(get_course_service)],
) -> list[Course]:
    """Retrieve all courses in the catalog (shared reference data accessible by all authenticated users)."""
    return await service.get_all()


@router.get("/{course_id}", response_model=Course)
async def get_course(
    course_id: str,
    _: Annotated[User, Depends(require_authenticated)],
    service: Annotated[CourseService, Depends(get_course_service)],
) -> Course:
    """Retrieve specific course definition by ID."""
    return await service.get_by_id(course_id=course_id)


@router.post("", response_model=Course, status_code=status.HTTP_201_CREATED)
async def create_course(
    course: Course,
    admin_user: Annotated[User, Depends(require_admin)],
    service: Annotated[CourseService, Depends(get_course_service)],
) -> Course:
    """Admin-only: Create a new course offering and record an audit log."""
    return await service.create(course=course, actor_id=admin_user.id)


@router.put("/{course_id}", response_model=Course)
async def update_course(
    course_id: str,
    course: Course,
    admin_user: Annotated[User, Depends(require_admin)],
    service: Annotated[CourseService, Depends(get_course_service)],
) -> Course:
    """Admin-only: Update course parameters and record an audit log."""
    return await service.update(
        course_id=course_id, course=course, actor_id=admin_user.id
    )


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(
    course_id: str,
    admin_user: Annotated[User, Depends(require_admin)],
    service: Annotated[CourseService, Depends(get_course_service)],
) -> None:
    """Admin-only: Remove a course offering and record an audit log."""
    await service.delete(course_id=course_id, actor_id=admin_user.id)

"""Sections API router with term filtering and administrative CRUD."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.security import require_admin, require_authenticated
from app.schemas.section import Section
from app.schemas.user import User
from app.services.section_service import SectionService

router = APIRouter(prefix="/sections", tags=["Sections"])


def get_section_service() -> SectionService:
    return SectionService()


@router.get("", response_model=list[Section])
async def list_sections(
    _: Annotated[User, Depends(require_authenticated)],
    service: Annotated[SectionService, Depends(get_section_service)],
    term: Annotated[
        str | None,
        Query(description="Optional academic term filter (e.g. 'Fall 2026')"),
    ] = None,
) -> list[Section]:
    """Retrieve all course sections, optionally filtered by academic term."""
    return await service.get_all(term=term)


@router.get("/{section_id}", response_model=Section)
async def get_section(
    section_id: str,
    _: Annotated[User, Depends(require_authenticated)],
    service: Annotated[SectionService, Depends(get_section_service)],
) -> Section:
    """Retrieve section parameters by ID."""
    return await service.get_by_id(section_id=section_id)


@router.post("", response_model=Section, status_code=status.HTTP_201_CREATED)
async def create_section(
    section: Section,
    admin_user: Annotated[User, Depends(require_admin)],
    service: Annotated[SectionService, Depends(get_section_service)],
) -> Section:
    """Admin-only: Create a new course section and record an audit log."""
    return await service.create(section=section, actor_id=admin_user.id)


@router.put("/{section_id}", response_model=Section)
async def update_section(
    section_id: str,
    section: Section,
    admin_user: Annotated[User, Depends(require_admin)],
    service: Annotated[SectionService, Depends(get_section_service)],
) -> Section:
    """Admin-only: Update section parameters and record an audit log."""
    return await service.update(
        section_id=section_id, section=section, actor_id=admin_user.id
    )


@router.delete("/{section_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_section(
    section_id: str,
    admin_user: Annotated[User, Depends(require_admin)],
    service: Annotated[SectionService, Depends(get_section_service)],
) -> None:
    """Admin-only: Remove a course section and record an audit log."""
    await service.delete(section_id=section_id, actor_id=admin_user.id)

"""Data persistence and repository layer for university workload management.

Provides unified data access whether running against local JSON storage or remote GitHub Gist.
"""

from __future__ import annotations

from typing import Any

from app.core.config import settings
from app.repositories.base import BaseStore, Repository
from app.repositories.gist_store import GistStore
from app.repositories.local_store import LocalStore
from app.schemas.assignment import Assignment
from app.schemas.audit import AuditLogEntry
from app.schemas.constraint import ConstraintRule
from app.schemas.course import Course
from app.schemas.faculty import Faculty
from app.schemas.override import Override
from app.schemas.resource import Resource
from app.schemas.section import Section
from app.schemas.timeslot import TimeSlot
from app.schemas.user import User

_STORE_INSTANCE: BaseStore | None = None


def get_store(backend: str | None = None) -> BaseStore:
    """Retrieve or initialize the active storage backend (LocalStore or GistStore)."""
    global _STORE_INSTANCE
    selected_backend = (backend or settings.STORE_BACKEND).lower()

    if _STORE_INSTANCE is None:
        if selected_backend == "gist":
            _STORE_INSTANCE = GistStore()
        else:
            _STORE_INSTANCE = LocalStore(seed_fallback_dir="data/seed")

    return _STORE_INSTANCE


def reset_store_instance() -> None:
    """Reset cached store instance (useful for testing different backends)."""
    global _STORE_INSTANCE
    _STORE_INSTANCE = None


# Typed Repository Factory Functions (compatible with FastAPI Depends)


def get_user_repository(store: BaseStore | None = None) -> Repository[User]:
    return Repository(store or get_store(), "users.json", User, id_field="id")


def get_faculty_repository(store: BaseStore | None = None) -> Repository[Faculty]:
    return Repository(store or get_store(), "faculty.json", Faculty, id_field="id")


def get_course_repository(store: BaseStore | None = None) -> Repository[Course]:
    return Repository(store or get_store(), "courses.json", Course, id_field="id")


def get_section_repository(store: BaseStore | None = None) -> Repository[Section]:
    return Repository(store or get_store(), "sections.json", Section, id_field="id")


def get_resource_repository(store: BaseStore | None = None) -> Repository[Resource]:
    return Repository(store or get_store(), "resources.json", Resource, id_field="id")


def get_timeslot_repository(store: BaseStore | None = None) -> Repository[TimeSlot]:
    return Repository(store or get_store(), "timeslots.json", TimeSlot, id_field="id")


def get_constraint_repository(
    store: BaseStore | None = None,
) -> Repository[ConstraintRule]:
    return Repository(
        store or get_store(), "constraints.json", ConstraintRule, id_field="rule_id"
    )


def get_assignment_repository(store: BaseStore | None = None) -> Repository[Assignment]:
    return Repository(
        store or get_store(), "assignments.json", Assignment, id_field="id"
    )


def get_override_repository(store: BaseStore | None = None) -> Repository[Override]:
    return Repository(store or get_store(), "overrides.json", Override, id_field="id")


def get_audit_repository(store: BaseStore | None = None) -> Repository[AuditLogEntry]:
    return Repository(
        store or get_store(), "audit_log.json", AuditLogEntry, id_field="id"
    )


def get_forecast_repository(
    store: BaseStore | None = None,
) -> Repository[dict[str, Any]]:
    return Repository(
        store or get_store(), "forecasts.json", dict, id_field="course_id"
    )


__all__ = [
    "BaseStore",
    "GistStore",
    "LocalStore",
    "Repository",
    "get_assignment_repository",
    "get_audit_repository",
    "get_constraint_repository",
    "get_course_repository",
    "get_faculty_repository",
    "get_forecast_repository",
    "get_override_repository",
    "get_resource_repository",
    "get_section_repository",
    "get_store",
    "get_timeslot_repository",
    "get_user_repository",
    "reset_store_instance",
]

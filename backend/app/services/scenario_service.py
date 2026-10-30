"""Scenario management service for loading evaluation fixtures and orchestrating active store state."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from app.core.errors import NotFoundError
from app.repositories import (
    get_assignment_repository,
    get_course_repository,
    get_faculty_repository,
    get_resource_repository,
    get_section_repository,
    get_timeslot_repository,
)
from app.schemas.assignment import Assignment
from app.schemas.course import Course
from app.schemas.faculty import Faculty
from app.schemas.resource import Resource
from app.schemas.section import Section
from app.schemas.timeslot import TimeSlot
from app.services.audit_service import AuditService

logger = logging.getLogger("app.services.scenario")


class ScenarioService:
    """Service orchestrating fixture scenario loading into active repository storage."""

    def __init__(
        self,
        fixtures_dir: Path | str | None = None,
        audit_service: AuditService | None = None,
    ) -> None:
        self.fixtures_dir = (
            Path(fixtures_dir).resolve()
            if fixtures_dir
            else Path("data/fixtures").resolve()
        )
        self.audit_service = audit_service or AuditService()

        # Repositories
        self.faculty_repo = get_faculty_repository()
        self.course_repo = get_course_repository()
        self.section_repo = get_section_repository()
        self.resource_repo = get_resource_repository()
        self.timeslot_repo = get_timeslot_repository()
        self.assignment_repo = get_assignment_repository()

    async def load_scenario(self, scenario_name: str, actor_id: str) -> dict[str, Any]:
        """Load an evaluation fixture from data/fixtures/ into active store and record audit log."""
        fixture_file = self.fixtures_dir / f"{scenario_name}.json"
        if not fixture_file.exists():
            raise NotFoundError(
                f"Evaluation fixture '{scenario_name}' not found at {fixture_file}"
            )

        try:
            raw_text = fixture_file.read_text(encoding="utf-8")
            data = json.loads(raw_text)
        except Exception as exc:
            logger.error(f"Failed to read fixture '{scenario_name}': {exc}")
            raise ValueError(f"Corrupted fixture file '{scenario_name}.json'") from exc

        expected_outcome = data.get("expected_outcome", {})
        scenario_data = data.get("scenario", {})
        assignments_data = data.get("assignments", [])

        # Validate domain entity payloads
        faculty_items = [
            Faculty.model_validate(f) for f in scenario_data.get("faculty", [])
        ]
        course_items = [
            Course.model_validate(c) for c in scenario_data.get("courses", [])
        ]
        section_items = [
            Section.model_validate(s) for s in scenario_data.get("sections", [])
        ]
        resource_items = [
            Resource.model_validate(r) for r in scenario_data.get("resources", [])
        ]
        timeslot_items = [
            TimeSlot.model_validate(ts) for ts in scenario_data.get("timeslots", [])
        ]
        assignment_items = [Assignment.model_validate(a) for a in assignments_data]

        # Bulk replace across repositories
        await self.faculty_repo.bulk_replace(faculty_items)
        await self.course_repo.bulk_replace(course_items)
        await self.section_repo.bulk_replace(section_items)
        await self.resource_repo.bulk_replace(resource_items)
        await self.timeslot_repo.bulk_replace(timeslot_items)
        await self.assignment_repo.bulk_replace(assignment_items)

        # Record audit log entry
        counts = {
            "faculty": len(faculty_items),
            "courses": len(course_items),
            "sections": len(section_items),
            "resources": len(resource_items),
            "timeslots": len(timeslot_items),
            "assignments": len(assignment_items),
        }
        await self.audit_service.log_event(
            actor_id=actor_id,
            action="SCENARIO_LOADED",
            entity="scenario",
            payload={
                "scenario_name": scenario_name,
                "feasible": expected_outcome.get("feasible"),
                "reason": expected_outcome.get("reason"),
                "counts": counts,
            },
        )

        return {
            "scenario_name": scenario_name,
            "expected_outcome": expected_outcome,
            "loaded_counts": counts,
            "message": f"Successfully loaded fixture '{scenario_name}' into active persistence store.",
        }

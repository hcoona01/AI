from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.assignment import Assignment
from app.schemas.common import RuleType
from app.schemas.course import Course
from app.schemas.faculty import Faculty
from app.schemas.resource import Resource
from app.schemas.section import Section
from app.schemas.timeslot import TimeSlot
from app.schemas.violation import Violation


class ConstraintRule(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    rule_id: str = Field(
        ...,
        min_length=2,
        description="Stable rule identifier (e.g., HC-01 or SC-01)",
    )
    type: RuleType = Field(..., description="Classification of rule (hard or soft)")
    description: str = Field(
        ...,
        min_length=1,
        description="Human-readable explanation of constraint rationale",
    )
    weight: float = Field(
        default=1.0,
        ge=0.0,
        description="Objective optimization penalty weight (applicable to soft constraints)",
    )
    enabled: bool = Field(
        default=True,
        description="Whether constraint is enforced during solver execution",
    )
    params: dict[str, Any] = Field(
        default_factory=dict,
        description="Configurable rule parameters (e.g., max_hours, penalty_scale)",
    )


class ValidationScenario(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    faculty: list[Faculty] = Field(
        default_factory=list, description="Available faculty members in scenario"
    )
    courses: list[Course] = Field(
        default_factory=list, description="Course catalog records"
    )
    sections: list[Section] = Field(
        default_factory=list,
        description="Course sections needing instructor assignment",
    )
    resources: list[Resource] = Field(
        default_factory=list, description="Classrooms and lab facilities"
    )
    timeslots: list[TimeSlot] = Field(
        default_factory=list, description="Available scheduling time slots"
    )
    previous_assignments: list[Assignment] = Field(
        default_factory=list,
        description="Historical or previous term assignments for continuity tracking",
    )


class ValidationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    assignments: list[Assignment] = Field(
        ..., description="Proposed course assignments to evaluate"
    )
    scenario: ValidationScenario = Field(
        ..., description="Scenario context (faculty, courses, sections, resources)"
    )
    rule_overrides: list[ConstraintRule] | None = Field(
        default=None,
        description="Optional custom weights or enabled states for this validation run",
    )


class ValidationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    is_valid: bool = Field(
        ..., description="True if no hard constraint violations exist"
    )
    hard_violation_count: int = Field(
        ..., ge=0, description="Number of hard rule violations"
    )
    soft_violation_count: int = Field(
        ..., ge=0, description="Number of soft rule penalties"
    )
    violations: list[Violation] = Field(
        default_factory=list, description="Detailed list of rule violations and repairs"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Evaluation timestamp",
    )


class ConstraintBatchUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    rules: list[ConstraintRule] = Field(
        ..., min_length=1, description="List of updated constraint rules"
    )

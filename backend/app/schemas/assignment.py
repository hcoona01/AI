from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import AssignmentSource


class Assignment(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: str = Field(
        ..., min_length=1, description="Unique assignment record identifier"
    )
    section_id: str = Field(
        ..., min_length=1, description="Course section instance assigned"
    )
    faculty_id: str = Field(
        ..., min_length=1, description="Faculty member assigned to section"
    )
    source: AssignmentSource = Field(
        ...,
        description="Origin of assignment (solver, baseline heuristic, or human override)",
    )
    fit_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Normalized faculty-to-course expertise match score between 0.0 and 1.0",
    )
    fit_breakdown: dict[str, float] = Field(
        default_factory=dict,
        description="Detailed fit component breakdown (e.g., tag_overlap, tfidf_syllabus, historical_eval)",
    )
    rule_ids_satisfied: list[str] = Field(
        default_factory=list,
        description="List of hard and soft rule_ids satisfied by this assignment",
    )
    rule_ids_violated: list[str] = Field(
        default_factory=list,
        description="List of soft rule_ids or overridden rules violated",
    )
    run_id: str = Field(
        ..., min_length=1, description="Solver optimization or batch process run ID"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp of assignment creation",
    )

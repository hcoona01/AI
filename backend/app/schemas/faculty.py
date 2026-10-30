from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

from app.schemas.common import FacultyRank


class FacultyExpertise(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    tag: str = Field(..., min_length=1, description="Subject domain or expertise tag")
    proficiency: int = Field(
        ...,
        ge=1,
        le=5,
        description="Competency rating from 1 (Novice) to 5 (Domain Master)",
    )


class Faculty(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: str = Field(..., min_length=1, description="Unique faculty member identifier")
    name: str = Field(..., min_length=1, description="Full name of faculty member")
    email: EmailStr = Field(..., description="Institutional contact email")
    rank: FacultyRank = Field(..., description="Academic appointment rank")
    expertise: list[FacultyExpertise] = Field(
        default_factory=list,
        description="Subject expertise tags and proficiency levels",
    )
    max_weekly_load_hours: float = Field(
        ...,
        gt=0,
        le=80.0,
        description="Contractual maximum weekly teaching/contact hours",
    )
    max_courses: int = Field(
        ...,
        ge=0,
        le=10,
        description="Maximum number of sections/courses assignable per term",
    )
    min_courses: int = Field(
        ...,
        ge=0,
        le=10,
        description="Minimum number of sections/courses required per term",
    )
    max_preparations: int = Field(
        ...,
        ge=0,
        le=10,
        description="Maximum unique course preparations allowed per term",
    )
    unavailable_slots: list[str] = Field(
        default_factory=list,
        description="List of TimeSlot IDs the faculty is unavailable for",
    )
    leave_terms: list[str] = Field(
        default_factory=list,
        description="List of academic terms on approved sabbatical/leave",
    )
    preferred_course_ids: list[str] = Field(
        default_factory=list, description="Course IDs preferred by faculty member"
    )

    @field_validator("expertise")
    @classmethod
    def validate_unique_expertise_tags(
        cls, v: list[FacultyExpertise]
    ) -> list[FacultyExpertise]:
        seen: set[str] = set()
        for item in v:
            tag_norm = item.tag.strip().lower()
            if tag_norm in seen:
                raise ValueError(f"Duplicate expertise tag '{item.tag}' is not allowed")
            seen.add(tag_norm)
        return v

    @model_validator(mode="after")
    def validate_course_limits(self) -> "Faculty":
        if self.max_courses < self.min_courses:
            raise ValueError(
                f"max_courses ({self.max_courses}) must be greater than or equal to min_courses ({self.min_courses})"
            )
        if self.max_courses > 0 and self.max_preparations > self.max_courses:
            raise ValueError(
                f"max_preparations ({self.max_preparations}) cannot exceed max_courses ({self.max_courses})"
            )
        return self

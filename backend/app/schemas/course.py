from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import CourseLevel


class Course(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: str = Field(..., min_length=1, description="Unique course identifier")
    code: str = Field(
        ..., min_length=2, description="Institutional course code (e.g., CS101)"
    )
    title: str = Field(..., min_length=1, description="Descriptive course title")
    description: str = Field(
        default="", description="Course syllabus overview or catalog description"
    )
    credits: int = Field(..., gt=0, le=20, description="Academic credits awarded")
    contact_hours: float = Field(
        ..., gt=0, le=40.0, description="Weekly instructional contact hours"
    )
    level: CourseLevel = Field(..., description="Curricular level of the course")
    required_tags: list[str] = Field(
        default_factory=list,
        description="Subject domain tags required to teach this course",
    )
    min_proficiency: int = Field(
        default=1,
        ge=1,
        le=5,
        description="Minimum instructor proficiency level required (1-5)",
    )
    is_lab: bool = Field(
        default=False, description="Whether course requires lab infrastructure"
    )
    required_resource_ids: list[str] = Field(
        default_factory=list,
        description="Required equipment or specific room resource IDs",
    )

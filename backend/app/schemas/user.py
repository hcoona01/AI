from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.schemas.common import UserRole


class User(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: str = Field(..., min_length=1, description="Unique user identifier")
    email: EmailStr = Field(..., description="Institutional email address")
    role: UserRole = Field(..., description="Role-based access level")
    faculty_id: str | None = Field(
        default=None, description="Linked faculty record ID if role is faculty"
    )

    @model_validator(mode="after")
    def validate_faculty_link(self) -> "User":
        if (
            self.role == UserRole.FACULTY
            and self.faculty_id is not None
            and not self.faculty_id.strip()
        ):
            raise ValueError(
                "faculty_id cannot be empty when provided for faculty role"
            )
        return self

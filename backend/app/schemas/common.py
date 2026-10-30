from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    FACULTY = "faculty"


class FacultyRank(str, Enum):
    PROFESSOR = "Professor"
    ASSOCIATE_PROFESSOR = "Associate Professor"
    ASSISTANT_PROFESSOR = "Assistant Professor"
    LECTURER = "Lecturer"
    ADJUNCT = "Adjunct"
    VISITING = "Visiting"


class CourseLevel(str, Enum):
    UNDERGRADUATE = "undergraduate"
    GRADUATE = "graduate"
    DOCTORAL = "doctoral"


class ResourceType(str, Enum):
    ROOM = "room"
    LAB = "lab"


class DayOfWeek(str, Enum):
    MON = "MON"
    TUE = "TUE"
    WED = "WED"
    THU = "THU"
    FRI = "FRI"
    SAT = "SAT"
    SUN = "SUN"


class RuleType(str, Enum):
    HARD = "hard"
    SOFT = "soft"


class AssignmentSource(str, Enum):
    SOLVER = "solver"
    BASELINE = "baseline"
    OVERRIDE = "override"


class ViolationSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

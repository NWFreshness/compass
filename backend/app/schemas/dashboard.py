import uuid
from pydantic import BaseModel


class ClassSummary(BaseModel):
    id: uuid.UUID
    name: str
    grade_level: int
    student_count: int
    avg_score: float | None
    tier_distribution: dict[str, int]

    model_config = {"from_attributes": True}


class AtRiskStudent(BaseModel):
    student_id: uuid.UUID
    student_name: str
    class_name: str
    avg_score: float
    tier: str

    model_config = {"from_attributes": True}


class GradeAverage(BaseModel):
    grade_level: int
    avg_score: float
    student_count: int

    model_config = {"from_attributes": True}


class SchoolSummary(BaseModel):
    id: uuid.UUID
    name: str
    student_count: int
    avg_score: float | None
    tier_distribution: dict[str, int]
    high_risk: bool

    model_config = {"from_attributes": True}


class TeacherDashboardResponse(BaseModel):
    classes: list[ClassSummary]
    at_risk: list[AtRiskStudent]


class PrincipalDashboardResponse(BaseModel):
    school_name: str
    total_students: int
    tier_distribution: dict[str, int]
    classes: list[ClassSummary]
    grade_averages: list[GradeAverage]
    at_risk: list[AtRiskStudent]


class DistrictDashboardResponse(BaseModel):
    total_students: int
    tier_distribution: dict[str, int]
    schools: list[SchoolSummary]

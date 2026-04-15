from typing import Optional
from pydantic import BaseModel


class SubjectAverage(BaseModel):
    subject_name: str
    average: float
    tier: str


class StudentReportData(BaseModel):
    student_name: str
    student_id_number: str
    grade_level: int
    class_name: Optional[str]
    school_name: str
    subject_averages: list[SubjectAverage]
    intervention_count: int
    latest_ai_recommendation: Optional[str]


class ClassStudentRow(BaseModel):
    student_name: str
    avg_score: Optional[float]
    tier: Optional[str]


class ClassReportData(BaseModel):
    class_name: str
    grade_level: int
    school_name: str
    students: list[ClassStudentRow]
    tier_distribution: dict[str, int]
    student_count: int


class ClassSummaryRow(BaseModel):
    class_name: str
    grade_level: int
    student_count: int
    avg_score: Optional[float]
    tier_distribution: dict[str, int]


class GradeAverageRow(BaseModel):
    grade_level: int
    avg_score: float
    student_count: int


class SchoolReportData(BaseModel):
    school_name: str
    total_students: int
    classes: list[ClassSummaryRow]
    grade_averages: list[GradeAverageRow]
    at_risk_count: int


class SchoolSummaryRow(BaseModel):
    school_name: str
    student_count: int
    avg_score: Optional[float]
    tier_distribution: dict[str, int]
    high_risk: bool


class DistrictReportData(BaseModel):
    total_students: int
    tier_distribution: dict[str, int]
    schools: list[SchoolSummaryRow]

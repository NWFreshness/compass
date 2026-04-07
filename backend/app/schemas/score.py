import uuid
from datetime import date
from typing import Optional
from pydantic import BaseModel, Field
from app.models import ScoreType


class ScoreCreate(BaseModel):
    student_id: uuid.UUID
    subject_id: uuid.UUID
    score_type: ScoreType
    value: float = Field(ge=0, le=100)
    date: date
    notes: Optional[str] = None


class ScoreResponse(BaseModel):
    id: uuid.UUID
    student_id: uuid.UUID
    subject_id: uuid.UUID
    score_type: ScoreType
    value: float
    date: date
    notes: Optional[str]
    model_config = {"from_attributes": True}


class CSVRowError(BaseModel):
    row: int
    message: str


class CSVImportResult(BaseModel):
    imported: int
    errors: list[CSVRowError]

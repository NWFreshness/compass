import uuid
from datetime import date
from typing import Optional
from pydantic import BaseModel, model_validator
from app.models import InterventionStatus


class InterventionCreate(BaseModel):
    student_id: Optional[uuid.UUID] = None
    class_id: Optional[uuid.UUID] = None
    strategy: str
    description: Optional[str] = None
    start_date: date
    outcome_notes: Optional[str] = None

    @model_validator(mode="after")
    def exactly_one_target(self):
        has_student = self.student_id is not None
        has_class = self.class_id is not None
        if has_student == has_class:
            raise ValueError("Exactly one of student_id or class_id must be provided")
        return self


class InterventionUpdate(BaseModel):
    status: Optional[InterventionStatus] = None
    description: Optional[str] = None
    outcome_notes: Optional[str] = None


class InterventionResponse(BaseModel):
    id: uuid.UUID
    student_id: Optional[uuid.UUID]
    class_id: Optional[uuid.UUID]
    teacher_id: uuid.UUID
    strategy: str
    description: Optional[str]
    start_date: date
    outcome_notes: Optional[str]
    status: InterventionStatus
    model_config = {"from_attributes": True}

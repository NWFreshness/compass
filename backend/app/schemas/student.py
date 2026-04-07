import uuid
from typing import Optional
from pydantic import BaseModel


class StudentCreate(BaseModel):
    name: str
    student_id_number: str
    grade_level: int
    school_id: uuid.UUID
    class_id: Optional[uuid.UUID] = None


class StudentUpdate(BaseModel):
    name: Optional[str] = None
    grade_level: Optional[int] = None
    school_id: Optional[uuid.UUID] = None
    class_id: Optional[uuid.UUID] = None


class StudentResponse(BaseModel):
    id: uuid.UUID
    name: str
    student_id_number: str
    grade_level: int
    school_id: uuid.UUID
    class_id: Optional[uuid.UUID]
    model_config = {"from_attributes": True}

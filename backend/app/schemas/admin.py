import uuid
from typing import Optional
from pydantic import BaseModel
from app.models import UserRole


class UserCreate(BaseModel):
    username: str
    password: str
    role: UserRole
    school_id: Optional[uuid.UUID] = None


class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None
    school_id: Optional[uuid.UUID] = None


class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    role: UserRole
    school_id: Optional[uuid.UUID]
    model_config = {"from_attributes": True}


class SchoolCreate(BaseModel):
    name: str
    address: Optional[str] = None


class SchoolResponse(BaseModel):
    id: uuid.UUID
    name: str
    address: Optional[str]
    model_config = {"from_attributes": True}


class ClassCreate(BaseModel):
    name: str
    grade_level: int
    school_id: uuid.UUID
    teacher_id: Optional[uuid.UUID] = None


class ClassResponse(BaseModel):
    id: uuid.UUID
    name: str
    grade_level: int
    school_id: uuid.UUID
    teacher_id: Optional[uuid.UUID]
    model_config = {"from_attributes": True}


class SubjectCreate(BaseModel):
    name: str


class SubjectResponse(BaseModel):
    id: uuid.UUID
    name: str
    model_config = {"from_attributes": True}

import uuid
from pydantic import BaseModel
from app.models import UserRole


class LoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    role: UserRole
    school_id: uuid.UUID | None

    model_config = {"from_attributes": True}

import uuid

from pydantic import BaseModel

from app.models.user import UserRole


class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    role: UserRole
    school_id: uuid.UUID | None

    model_config = {"from_attributes": True}

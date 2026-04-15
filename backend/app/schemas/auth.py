from pydantic import BaseModel

from app.schemas.shared import UserResponse


class LoginRequest(BaseModel):
    username: str
    password: str



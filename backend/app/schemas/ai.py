import uuid
from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel


class AIRecommendationResponse(BaseModel):
    id: uuid.UUID
    target_type: Literal["student", "class"]
    student_id: Optional[uuid.UUID]
    class_id: Optional[uuid.UUID]
    created_by: uuid.UUID
    model_name: str
    temperature: float
    prompt: str
    response: str
    snapshot: dict[str, Any]
    parse_error: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class AuditLogEntry(BaseModel):
    id: uuid.UUID
    user_id: Optional[uuid.UUID]
    action: str
    entity_type: str
    entity_id: Optional[str]
    detail: Optional[str]
    school_id: Optional[uuid.UUID]
    timestamp: datetime
    model_config = {"from_attributes": True}


class AuditLogPage(BaseModel):
    total: int
    entries: list[AuditLogEntry]

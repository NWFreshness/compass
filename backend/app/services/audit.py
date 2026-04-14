import uuid
from typing import Optional
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog


def log_action(
    db: Session,
    *,
    user_id: Optional[uuid.UUID],
    action: str,
    entity_type: str,
    entity_id: Optional[str] = None,
    detail: Optional[str] = None,
    school_id: Optional[uuid.UUID] = None,
) -> None:
    """Append an audit entry to the session. The caller's db.commit() persists it."""
    entry = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        detail=detail,
        school_id=school_id,
    )
    db.add(entry)

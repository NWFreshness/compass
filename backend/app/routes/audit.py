from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.middleware.auth import require_role
from app.models import AuditLog, User, UserRole
from app.schemas.audit import AuditLogPage

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("", response_model=AuditLogPage)
def list_audit_log(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.it_admin, UserRole.district_admin)),
) -> AuditLogPage:
    q = db.query(AuditLog)

    if current_user.role == UserRole.district_admin:
        q = q.filter(AuditLog.school_id == current_user.school_id)

    if action:
        q = q.filter(AuditLog.action == action)
    if entity_type:
        q = q.filter(AuditLog.entity_type == entity_type)
    if date_from:
        q = q.filter(AuditLog.timestamp >= date_from)
    if date_to:
        q = q.filter(AuditLog.timestamp <= date_to)

    total = q.count()
    entries = q.order_by(AuditLog.timestamp.desc()).offset((page - 1) * per_page).limit(per_page).all()
    return AuditLogPage(total=total, entries=entries)

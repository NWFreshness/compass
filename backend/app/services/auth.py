import uuid
from datetime import datetime, timedelta, timezone
import bcrypt
from sqlalchemy.orm import Session
from app.models import User, UserSession
from app.config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_session(db: Session, user: User) -> UserSession:
    session = UserSession(
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=settings.session_expiry_hours),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_session(db: Session, session_id: str) -> UserSession | None:
    try:
        sid = uuid.UUID(session_id)
    except ValueError:
        return None
    session = db.query(UserSession).filter(UserSession.id == sid).first()
    if session and session.expires_at.replace(tzinfo=timezone.utc) > datetime.now(timezone.utc):
        return session
    return None


def delete_session(db: Session, session_id: str) -> None:
    try:
        sid = uuid.UUID(session_id)
    except ValueError:
        return
    db.query(UserSession).filter(UserSession.id == sid).delete()
    db.commit()

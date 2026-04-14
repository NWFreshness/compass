from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from app.db import get_db
from app.middleware.auth import get_current_user
from app.models import User
from app.schemas.auth import LoginRequest, UserResponse
from app.services.audit import log_action
from app.services.auth import create_session, delete_session, verify_password
from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=UserResponse)
def login(body: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    session = create_session(db, user)
    response.set_cookie(
        key="session_id",
        value=str(session.id),
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
    )
    log_action(db, user_id=user.id, action="login", entity_type="user", entity_id=str(user.id), school_id=user.school_id)
    db.commit()
    return user


@router.post("/logout")
def logout(response: Response, session_id: str | None = Cookie(default=None), db: Session = Depends(get_db)):
    if session_id:
        delete_session(db, session_id)
        log_action(db, user_id=None, action="logout", entity_type="session", entity_id=session_id)
        db.commit()
    response.delete_cookie(
        key="session_id",
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
    )
    return {"ok": True}


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user

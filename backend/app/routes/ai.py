import json
import uuid
from collections.abc import Iterator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.middleware.auth import get_current_user
from app.models import Class, Student, User, UserRole
from app.schemas.ai import AIRecommendationResponse
from app.services.ai_analysis import (
    analyze_class,
    analyze_class_stream,
    analyze_student,
    analyze_student_stream,
    list_class_history,
    list_student_history,
)

router = APIRouter(prefix="/api/ai", tags=["ai"])


def _require_student_scope(db: Session, current_user: User, student_id: uuid.UUID) -> Student:
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    if current_user.role == UserRole.teacher:
        class_ids = [c.id for c in db.query(Class).filter(Class.teacher_id == current_user.id).all()]
        if student.class_id not in class_ids:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
    elif current_user.role == UserRole.principal:
        if student.school_id != current_user.school_id:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
    return student


def _require_class_scope(db: Session, current_user: User, class_id: uuid.UUID) -> Class:
    cls = db.query(Class).filter(Class.id == class_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
    if current_user.role == UserRole.teacher:
        if cls.teacher_id != current_user.id:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
    elif current_user.role == UserRole.principal:
        if cls.school_id != current_user.school_id:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
    return cls


@router.post(
    "/student/{student_id}/analyze",
    response_model=AIRecommendationResponse,
    status_code=status.HTTP_201_CREATED,
)
def analyze_student_route(
    student_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_student_scope(db, current_user, student_id)
    return analyze_student(db, student_id=student_id, created_by=current_user.id)


@router.get("/student/{student_id}/history", response_model=list[AIRecommendationResponse])
def student_history_route(
    student_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_student_scope(db, current_user, student_id)
    return list_student_history(db, student_id)


@router.post(
    "/class/{class_id}/analyze",
    response_model=AIRecommendationResponse,
    status_code=status.HTTP_201_CREATED,
)
def analyze_class_route(
    class_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_class_scope(db, current_user, class_id)
    return analyze_class(db, class_id=class_id, created_by=current_user.id)


@router.get("/class/{class_id}/history", response_model=list[AIRecommendationResponse])
def class_history_route(
    class_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_class_scope(db, current_user, class_id)
    return list_class_history(db, class_id)


def _sse_stream(gen: Iterator[str]):
    """Wrap a token generator as SSE, encoding each payload as JSON."""
    try:
        for token in gen:
            yield f"data: {json.dumps(token)}\n\n"
    except Exception as exc:
        yield f"data: {json.dumps({'__error__': str(exc)})}\n\n"


@router.post("/student/{student_id}/analyze/stream")
def analyze_student_stream_route(
    student_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_student_scope(db, current_user, student_id)
    gen = analyze_student_stream(db, student_id=student_id, created_by=current_user.id)
    return StreamingResponse(_sse_stream(gen), media_type="text/event-stream")


@router.post("/class/{class_id}/analyze/stream")
def analyze_class_stream_route(
    class_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_class_scope(db, current_user, class_id)
    gen = analyze_class_stream(db, class_id=class_id, created_by=current_user.id)
    return StreamingResponse(_sse_stream(gen), media_type="text/event-stream")

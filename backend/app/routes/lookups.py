from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.middleware.auth import get_current_user
from app.models import Class, School, Subject, User, UserRole
from app.schemas.admin import ClassResponse, SchoolResponse, SubjectResponse

router = APIRouter(prefix="/api/lookups", tags=["lookups"])


@router.get("/schools", response_model=list[SchoolResponse])
def list_schools(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(School)
    if current_user.role in {UserRole.principal, UserRole.teacher}:
        query = query.filter(School.id == current_user.school_id)
    return query.order_by(School.name.asc()).all()


@router.get("/classes", response_model=list[ClassResponse])
def list_classes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Class)
    if current_user.role == UserRole.teacher:
        query = query.filter(Class.teacher_id == current_user.id)
    elif current_user.role == UserRole.principal:
        query = query.filter(Class.school_id == current_user.school_id)
    return query.order_by(Class.grade_level.asc(), Class.name.asc()).all()


@router.get("/subjects", response_model=list[SubjectResponse])
def list_subjects(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return db.query(Subject).order_by(Subject.name.asc()).all()

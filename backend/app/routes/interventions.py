import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.middleware.auth import get_current_user
from app.models import Class, Intervention, InterventionStatus, Student, User, UserRole
from app.schemas.intervention import InterventionCreate, InterventionResponse, InterventionUpdate

router = APIRouter(prefix="/api/interventions", tags=["interventions"])


def _assert_can_write(db: Session, user: User, intervention: Intervention) -> None:
    """Raise 403 if user cannot create/modify this intervention."""
    if user.role in (UserRole.it_admin, UserRole.district_admin):
        return
    if user.role == UserRole.principal:
        # must be within the principal's school
        if intervention.student_id:
            student = db.query(Student).filter(Student.id == intervention.student_id).first()
            if not student or student.school_id != user.school_id:
                raise HTTPException(status_code=403, detail="Outside your school")
        elif intervention.class_id:
            cls = db.query(Class).filter(Class.id == intervention.class_id).first()
            if not cls or cls.school_id != user.school_id:
                raise HTTPException(status_code=403, detail="Outside your school")
        return
    if user.role == UserRole.teacher:
        if intervention.student_id:
            # student must be in one of teacher's classes
            student = db.query(Student).filter(Student.id == intervention.student_id).first()
            if not student:
                raise HTTPException(status_code=403, detail="Student not found")
            cls = db.query(Class).filter(Class.id == student.class_id, Class.teacher_id == user.id).first()
            if not cls:
                raise HTTPException(status_code=403, detail="Student is not in your class")
        elif intervention.class_id:
            cls = db.query(Class).filter(Class.id == intervention.class_id, Class.teacher_id == user.id).first()
            if not cls:
                raise HTTPException(status_code=403, detail="You do not teach this class")
        return
    raise HTTPException(status_code=403, detail="Insufficient permissions")


def _scoped_query(db: Session, user: User):
    q = db.query(Intervention)
    if user.role == UserRole.teacher:
        class_ids = [c.id for c in db.query(Class).filter(Class.teacher_id == user.id).all()]
        student_ids = [s.id for s in db.query(Student).filter(Student.class_id.in_(class_ids)).all()]
        q = q.filter(
            (Intervention.student_id.in_(student_ids)) | (Intervention.class_id.in_(class_ids))
        )
    elif user.role == UserRole.principal:
        class_ids = [c.id for c in db.query(Class).filter(Class.school_id == user.school_id).all()]
        student_ids = [s.id for s in db.query(Student).filter(Student.school_id == user.school_id).all()]
        q = q.filter(
            (Intervention.student_id.in_(student_ids)) | (Intervention.class_id.in_(class_ids))
        )
    return q


@router.get("", response_model=list[InterventionResponse])
def list_interventions(
    student_id: Optional[uuid.UUID] = None,
    class_id: Optional[uuid.UUID] = None,
    status: Optional[InterventionStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = _scoped_query(db, current_user)
    if student_id:
        q = q.filter(Intervention.student_id == student_id)
    if class_id:
        q = q.filter(Intervention.class_id == class_id)
    if status:
        q = q.filter(Intervention.status == status)
    return q.order_by(
        Intervention.status.asc(),  # active < resolved alphabetically
        Intervention.start_date.desc(),
    ).all()


@router.post("", response_model=InterventionResponse, status_code=201)
def create_intervention(
    body: InterventionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    intervention = Intervention(
        **body.model_dump(),
        teacher_id=current_user.id,
        status=InterventionStatus.active,
    )
    _assert_can_write(db, current_user, intervention)
    db.add(intervention)
    db.commit()
    db.refresh(intervention)
    return intervention


@router.patch("/{intervention_id}", response_model=InterventionResponse)
def update_intervention(
    intervention_id: uuid.UUID,
    body: InterventionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    intervention = db.query(Intervention).filter(Intervention.id == intervention_id).first()
    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention not found")
    _assert_can_write(db, current_user, intervention)
    for field, val in body.model_dump(exclude_none=True).items():
        setattr(intervention, field, val)
    db.commit()
    db.refresh(intervention)
    return intervention

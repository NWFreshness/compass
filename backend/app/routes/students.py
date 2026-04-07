import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.middleware.auth import get_current_user, require_role
from app.models import Student, User, UserRole, Class
from app.schemas.student import StudentCreate, StudentResponse, StudentUpdate

router = APIRouter(prefix="/api/students", tags=["students"])


def _scoped_query(db: Session, user: User):
    q = db.query(Student)
    if user.role == UserRole.teacher:
        class_ids = [c.id for c in db.query(Class).filter(Class.teacher_id == user.id).all()]
        q = q.filter(Student.class_id.in_(class_ids))
    elif user.role == UserRole.principal:
        q = q.filter(Student.school_id == user.school_id)
    # district_admin and it_admin see all
    return q


@router.get("", response_model=list[StudentResponse])
def list_students(
    search: str | None = None,
    page: int = 1,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = _scoped_query(db, current_user)
    if search:
        q = q.filter(Student.name.ilike(f"%{search}%"))
    return q.offset((page - 1) * 50).limit(50).all()


@router.get("/{student_id}", response_model=StudentResponse)
def get_student(
    student_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    student = _scoped_query(db, current_user).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@router.post("", response_model=StudentResponse, status_code=201)
def create_student(
    body: StudentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.district_admin:
        raise HTTPException(status_code=403, detail="District admins cannot create students")
    if current_user.role == UserRole.principal:
        if body.school_id != current_user.school_id:
            raise HTTPException(status_code=403, detail="Cannot create student outside your school")
    if current_user.role == UserRole.teacher:
        # teacher may only create students in their own assigned classes
        if body.class_id is not None:
            cls = db.query(Class).filter(Class.id == body.class_id, Class.teacher_id == current_user.id).first()
            if not cls:
                raise HTTPException(status_code=403, detail="Cannot create student in a class you do not teach")
        else:
            raise HTTPException(status_code=403, detail="Teachers must assign a class when creating a student")
    student = Student(**body.model_dump())
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


@router.patch("/{student_id}", response_model=StudentResponse)
def update_student(
    student_id: uuid.UUID,
    body: StudentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    student = _scoped_query(db, current_user).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    for field, val in body.model_dump(exclude_none=True).items():
        setattr(student, field, val)
    db.commit()
    db.refresh(student)
    return student

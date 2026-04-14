import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db import get_db
from app.middleware.auth import require_role
from app.models import User, UserRole, School, Class, Subject
from app.schemas.admin import (
    ClassCreate, ClassResponse, SchoolCreate, SchoolResponse,
    SubjectCreate, SubjectResponse, UserCreate, UserResponse, UserUpdate,
)
from app.services.audit import log_action
from app.services.auth import hash_password

router = APIRouter(prefix="/api/admin", tags=["admin"])
admin_only = Depends(require_role(UserRole.it_admin))


@router.get("/users", response_model=list[UserResponse], dependencies=[admin_only])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).all()


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(body: UserCreate, db: Session = Depends(get_db), current_user: User = Depends(require_role(UserRole.it_admin))):
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(status_code=409, detail="Username already exists")
    user = User(
        username=body.username,
        hashed_password=hash_password(body.password),
        role=body.role,
        school_id=body.school_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    log_action(db, user_id=current_user.id, action="user.create", entity_type="user", entity_id=str(user.id))
    db.commit()
    return user


@router.patch("/users/{user_id}", response_model=UserResponse, dependencies=[admin_only])
def update_user(user_id: uuid.UUID, body: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if body.username is not None:
        user.username = body.username
    if body.password is not None:
        user.hashed_password = hash_password(body.password)
    if body.role is not None:
        user.role = body.role
    if body.school_id is not None:
        user.school_id = body.school_id
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(require_role(UserRole.it_admin))):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Null out teacher assignment on any classes this user teaches
    db.query(Class).filter(Class.teacher_id == user_id).update({"teacher_id": None})
    db.delete(user)
    db.commit()
    log_action(db, user_id=current_user.id, action="user.delete", entity_type="user", entity_id=str(user_id))
    db.commit()


@router.get("/schools", response_model=list[SchoolResponse], dependencies=[admin_only])
def list_schools(db: Session = Depends(get_db)):
    return db.query(School).all()


@router.post("/schools", response_model=SchoolResponse, status_code=201, dependencies=[admin_only])
def create_school(body: SchoolCreate, db: Session = Depends(get_db)):
    school = School(**body.model_dump())
    db.add(school)
    db.commit()
    db.refresh(school)
    return school


@router.get("/classes", response_model=list[ClassResponse], dependencies=[admin_only])
def list_classes(db: Session = Depends(get_db)):
    return db.query(Class).all()


@router.post("/classes", response_model=ClassResponse, status_code=201, dependencies=[admin_only])
def create_class(body: ClassCreate, db: Session = Depends(get_db)):
    cls = Class(**body.model_dump())
    db.add(cls)
    db.commit()
    db.refresh(cls)
    return cls


@router.get("/subjects", response_model=list[SubjectResponse], dependencies=[admin_only])
def list_subjects(db: Session = Depends(get_db)):
    return db.query(Subject).all()


@router.post("/subjects", response_model=SubjectResponse, status_code=201, dependencies=[admin_only])
def create_subject(body: SubjectCreate, db: Session = Depends(get_db)):
    subject = Subject(**body.model_dump())
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return subject

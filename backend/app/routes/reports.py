import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db import get_db
from app.middleware.auth import get_current_user, require_role
from app.models import Class, School, Student, User, UserRole
from app.services.reports import (
    build_class_report_data, build_district_report_data,
    build_school_report_data, build_student_report_data,
    to_csv_class, to_csv_district, to_csv_school, to_csv_student,
    to_pdf_class, to_pdf_district, to_pdf_school, to_pdf_student,
)

router = APIRouter(prefix="/api/reports", tags=["reports"])

Format = Literal["csv", "pdf"]


def _csv_response(content: str, filename: str) -> Response:
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


def _pdf_response(content: bytes, filename: str) -> Response:
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


def _assert_student_access(db: Session, user: User, student: Student) -> None:
    if user.role in (UserRole.it_admin, UserRole.district_admin):
        return
    if user.role == UserRole.principal:
        if student.school_id != user.school_id:
            raise HTTPException(status_code=403, detail="Outside your school")
        return
    if user.role == UserRole.teacher:
        class_ids = [c.id for c in db.query(Class).filter(Class.teacher_id == user.id).all()]
        if student.class_id not in class_ids:
            raise HTTPException(status_code=403, detail="Student is not in your class")
        return
    raise HTTPException(status_code=403, detail="Insufficient permissions")


def _assert_class_access(db: Session, user: User, cls: Class) -> None:
    if user.role in (UserRole.it_admin, UserRole.district_admin):
        return
    if user.role == UserRole.principal:
        if cls.school_id != user.school_id:
            raise HTTPException(status_code=403, detail="Outside your school")
        return
    if user.role == UserRole.teacher:
        if cls.teacher_id != user.id:
            raise HTTPException(status_code=403, detail="You do not teach this class")
        return
    raise HTTPException(status_code=403, detail="Insufficient permissions")


def _assert_school_access(user: User, school: School) -> None:
    if user.role in (UserRole.it_admin, UserRole.district_admin):
        return
    if user.role == UserRole.principal:
        if school.id != user.school_id:
            raise HTTPException(status_code=403, detail="Outside your school")
        return
    raise HTTPException(status_code=403, detail="Insufficient permissions")


@router.get("/student/{student_id}")
def student_report(
    student_id: uuid.UUID,
    format: Format = Query("csv"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    _assert_student_access(db, current_user, student)
    data = build_student_report_data(db, student)
    slug = student.student_id_number
    if format == "pdf":
        return _pdf_response(to_pdf_student(data), f"student_{slug}.pdf")
    return _csv_response(to_csv_student(data), f"student_{slug}.csv")


@router.get("/class/{class_id}")
def class_report(
    class_id: uuid.UUID,
    format: Format = Query("csv"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    cls = db.query(Class).filter(Class.id == class_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
    _assert_class_access(db, current_user, cls)
    data = build_class_report_data(db, cls)
    slug = cls.name.replace(" ", "_")
    if format == "pdf":
        return _pdf_response(to_pdf_class(data), f"class_{slug}.pdf")
    return _csv_response(to_csv_class(data), f"class_{slug}.csv")


@router.get("/school/{school_id}")
def school_report(
    school_id: uuid.UUID,
    format: Format = Query("csv"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    _assert_school_access(current_user, school)
    data = build_school_report_data(db, school)
    slug = school.name.replace(" ", "_")
    if format == "pdf":
        return _pdf_response(to_pdf_school(data), f"school_{slug}.pdf")
    return _csv_response(to_csv_school(data), f"school_{slug}.csv")


@router.get("/district")
def district_report(
    format: Format = Query("csv"),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.it_admin, UserRole.district_admin)
    ),
) -> Response:
    data = build_district_report_data(db)
    if format == "pdf":
        return _pdf_response(to_pdf_district(data), "district_report.pdf")
    return _csv_response(to_csv_district(data), "district_report.csv")

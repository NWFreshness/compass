from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db import get_db
from app.middleware.auth import get_current_user, require_role
from app.models import Class, School, User, UserRole
from app.schemas.dashboard import (
    TeacherDashboardResponse, PrincipalDashboardResponse, DistrictDashboardResponse,
    ClassSummary, SchoolSummary,
)
from app.services.dashboard import (
    get_class_summary, get_at_risk_students, get_grade_averages, get_school_summary,
)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/teacher", response_model=TeacherDashboardResponse)
def teacher_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.it_admin)),
):
    classes = db.query(Class).filter(Class.teacher_id == current_user.id).all()
    class_summaries = []
    for cls in classes:
        summary = get_class_summary(db, cls.id)
        class_summaries.append(ClassSummary(
            id=cls.id,
            name=cls.name,
            grade_level=cls.grade_level,
            **summary,
        ))
    at_risk = get_at_risk_students(db, [cls.id for cls in classes])
    return TeacherDashboardResponse(classes=class_summaries, at_risk=at_risk)


@router.get("/principal", response_model=PrincipalDashboardResponse)
def principal_dashboard(
    school_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.principal, UserRole.it_admin, UserRole.district_admin)),
):
    import uuid
    # Resolve school
    if current_user.role == UserRole.principal:
        resolved_school_id = current_user.school_id
    else:
        if not school_id:
            raise HTTPException(status_code=400, detail="school_id query param required for this role")
        try:
            resolved_school_id = uuid.UUID(school_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid school_id")

    if not resolved_school_id:
        raise HTTPException(status_code=400, detail="No school assigned")

    school = db.query(School).filter(School.id == resolved_school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")

    classes = db.query(Class).filter(Class.school_id == resolved_school_id).all()
    class_summaries = []
    for cls in classes:
        summary = get_class_summary(db, cls.id)
        class_summaries.append(ClassSummary(
            id=cls.id,
            name=cls.name,
            grade_level=cls.grade_level,
            **summary,
        ))

    school_summary = get_school_summary(db, resolved_school_id)
    grade_averages = get_grade_averages(db, resolved_school_id)
    at_risk = get_at_risk_students(db, [cls.id for cls in classes])

    return PrincipalDashboardResponse(
        school_name=school.name,
        total_students=school_summary["student_count"],
        tier_distribution=school_summary["tier_distribution"],
        classes=class_summaries,
        grade_averages=grade_averages,
        at_risk=at_risk,
    )


@router.get("/district", response_model=DistrictDashboardResponse)
def district_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.district_admin, UserRole.it_admin)),
):
    schools = db.query(School).all()
    school_summaries = []
    total_students = 0
    district_tiers = {"tier1": 0, "tier2": 0, "tier3": 0}

    for school in schools:
        summary = get_school_summary(db, school.id)
        school_summaries.append(SchoolSummary(
            id=school.id,
            name=school.name,
            **summary,
        ))
        total_students += summary["student_count"]
        for tier, count in summary["tier_distribution"].items():
            district_tiers[tier] += count

    return DistrictDashboardResponse(
        total_students=total_students,
        tier_distribution=district_tiers,
        schools=school_summaries,
    )

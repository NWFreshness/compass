from datetime import date
import pytest
from app.models import (
    Base, Class, School, Score, ScoreType, Student, Subject, User, UserRole,
    Intervention, InterventionStatus,
)
from app.schemas.reports import (
    StudentReportData, ClassReportData, SchoolReportData, DistrictReportData,
)
from app.services.reports import (
    build_student_report_data, build_class_report_data,
    build_school_report_data, build_district_report_data,
)
from app.services.auth import hash_password
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


def make_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)(), engine


def seed_report_world(db):
    school = School(name="Test School")
    db.add(school)
    db.flush()
    math = Subject(name="Math")
    reading = Subject(name="Reading")
    db.add_all([math, reading])
    db.flush()
    teacher = User(
        username="report_teacher",
        hashed_password=hash_password("pw"),
        role=UserRole.teacher,
        school_id=school.id,
    )
    db.add(teacher)
    db.flush()
    cls = Class(name="3A", grade_level=3, school_id=school.id, teacher_id=teacher.id)
    db.add(cls)
    db.flush()
    student = Student(
        name="Alice",
        student_id_number="A001",
        grade_level=3,
        school_id=school.id,
        class_id=cls.id,
    )
    db.add(student)
    db.flush()
    db.add_all([
        Score(student_id=student.id, subject_id=math.id, score_type=ScoreType.quiz, value=85.0, date=date(2026, 3, 1)),
        Score(student_id=student.id, subject_id=math.id, score_type=ScoreType.test, value=75.0, date=date(2026, 3, 15)),
        Score(student_id=student.id, subject_id=reading.id, score_type=ScoreType.quiz, value=60.0, date=date(2026, 3, 5)),
    ])
    db.commit()
    return {
        "school": school, "math": math, "reading": reading,
        "teacher": teacher, "cls": cls, "student": student,
    }


def test_build_student_report_data_returns_subject_averages():
    db, engine = make_db()
    try:
        world = seed_report_world(db)
        data = build_student_report_data(db, world["student"])
        assert isinstance(data, StudentReportData)
        assert data.student_name == "Alice"
        assert data.grade_level == 3
        subject_names = {s.subject_name for s in data.subject_averages}
        assert "Math" in subject_names
        assert "Reading" in subject_names
        math_avg = next(s for s in data.subject_averages if s.subject_name == "Math")
        assert math_avg.average == pytest.approx(80.0)
        assert math_avg.tier == "tier1"
        reading_avg = next(s for s in data.subject_averages if s.subject_name == "Reading")
        assert reading_avg.tier == "tier3"
    finally:
        db.close()
        engine.dispose()


def test_build_class_report_data_includes_all_students():
    db, engine = make_db()
    try:
        world = seed_report_world(db)
        data = build_class_report_data(db, world["cls"])
        assert isinstance(data, ClassReportData)
        assert data.class_name == "3A"
        assert data.student_count == 1
        assert len(data.students) == 1
        assert data.students[0].student_name == "Alice"
    finally:
        db.close()
        engine.dispose()


def test_build_school_report_data():
    db, engine = make_db()
    try:
        world = seed_report_world(db)
        data = build_school_report_data(db, world["school"])
        assert isinstance(data, SchoolReportData)
        assert data.school_name == "Test School"
        assert data.total_students == 1
        assert len(data.classes) == 1
    finally:
        db.close()
        engine.dispose()


def test_build_district_report_data():
    db, engine = make_db()
    try:
        world = seed_report_world(db)
        data = build_district_report_data(db)
        assert isinstance(data, DistrictReportData)
        assert data.total_students >= 1
        assert len(data.schools) >= 1
    finally:
        db.close()
        engine.dispose()


# ---------------------------------------------------------------------------
# Route tests (appended in Task 2)
# ---------------------------------------------------------------------------

from app.services.auth import hash_password as _hp


def seed_for_routes(db):
    school = School(name="Route School")
    db.add(school)
    db.flush()
    subj = Subject(name="Science")
    db.add(subj)
    db.flush()
    teacher = User(username="r_teacher", hashed_password=_hp("pw"), role=UserRole.teacher, school_id=school.id)
    principal = User(username="r_principal", hashed_password=_hp("pw"), role=UserRole.principal, school_id=school.id)
    it_admin = User(username="r_admin", hashed_password=_hp("pw"), role=UserRole.it_admin)
    db.add_all([teacher, principal, it_admin])
    db.flush()
    cls = Class(name="5B", grade_level=5, school_id=school.id, teacher_id=teacher.id)
    db.add(cls)
    db.flush()
    student = Student(name="Bob", student_id_number="B002", grade_level=5, school_id=school.id, class_id=cls.id)
    db.add(student)
    db.flush()
    db.add(Score(student_id=student.id, subject_id=subj.id, score_type=ScoreType.quiz, value=88.0, date=date(2026, 4, 1)))
    db.commit()
    return {"school": school, "cls": cls, "student": student, "teacher": teacher, "it_admin": it_admin}


def login_as(client, username):
    r = client.post("/api/auth/login", json={"username": username, "password": "pw"})
    assert r.status_code == 200


def test_student_report_csv_returns_csv(client, db):
    world = seed_for_routes(db)
    login_as(client, "r_teacher")
    r = client.get(f"/api/reports/student/{world['student'].id}?format=csv")
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]


def test_student_report_pdf_returns_pdf(client, db):
    world = seed_for_routes(db)
    login_as(client, "r_teacher")
    r = client.get(f"/api/reports/student/{world['student'].id}?format=pdf")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"


def test_class_report_csv(client, db):
    world = seed_for_routes(db)
    login_as(client, "r_teacher")
    r = client.get(f"/api/reports/class/{world['cls'].id}?format=csv")
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]


def test_school_report_csv(client, db):
    world = seed_for_routes(db)
    login_as(client, "r_principal")
    r = client.get(f"/api/reports/school/{world['school'].id}?format=csv")
    assert r.status_code == 200


def test_district_report_requires_admin(client, db):
    seed_for_routes(db)
    login_as(client, "r_teacher")
    r = client.get("/api/reports/district?format=csv")
    assert r.status_code == 403


def test_district_report_csv_for_admin(client, db):
    seed_for_routes(db)
    login_as(client, "r_admin")
    r = client.get("/api/reports/district?format=csv")
    assert r.status_code == 200


def test_report_requires_auth(client, db):
    world = seed_for_routes(db)
    r = client.get(f"/api/reports/student/{world['student'].id}?format=csv")
    assert r.status_code == 401

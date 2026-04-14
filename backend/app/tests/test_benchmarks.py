from datetime import date

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import Base, Benchmark, Class, School, Student, Subject, User, UserRole
from app.schemas.benchmark import BenchmarkCreate, BenchmarkUpdate
from app.services.auth import hash_password
from app.services.mtss import get_student_tier


def seed_benchmark_world(db):
    school = School(name="Benchmark School")
    subject = Subject(name="Math")
    reading = Subject(name="Reading")
    db.add_all([school, subject, reading])
    db.flush()
    it_admin = User(username="it_admin", hashed_password=hash_password("password1"), role=UserRole.it_admin)
    district_admin = User(
        username="district_admin",
        hashed_password=hash_password("password1"),
        role=UserRole.district_admin,
    )
    principal = User(
        username="principal",
        hashed_password=hash_password("password1"),
        role=UserRole.principal,
        school_id=school.id,
    )
    teacher = User(
        username="teacher",
        hashed_password=hash_password("password1"),
        role=UserRole.teacher,
        school_id=school.id,
    )
    db.add_all([it_admin, district_admin, principal, teacher])
    db.flush()
    cls = Class(name="4A", grade_level=4, school_id=school.id, teacher_id=teacher.id)
    db.add(cls)
    db.flush()
    student = Student(
        name="Benchmark Student",
        student_id_number="B100",
        grade_level=4,
        school_id=school.id,
        class_id=cls.id,
    )
    db.add(student)
    db.commit()
    return {
        "school": school,
        "subject": subject,
        "reading": reading,
        "it_admin": it_admin,
        "district_admin": district_admin,
        "principal": principal,
        "teacher": teacher,
        "class": cls,
        "student": student,
    }


def login(client, username: str):
    response = client.post("/api/auth/login", json={"username": username, "password": "password1"})
    assert response.status_code == 200
    return response


def make_isolated_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    return session, engine


def test_benchmark_create_rejects_invalid_threshold_order():
    with pytest.raises(ValidationError):
        BenchmarkCreate(
            grade_level=4,
            subject_id="11111111-1111-1111-1111-111111111111",
            tier1_min=65,
            tier2_min=70,
        )


def test_benchmark_update_rejects_invalid_threshold_order():
    with pytest.raises(ValidationError):
        BenchmarkUpdate(tier1_min=65, tier2_min=70)


def test_duplicate_grade_and_subject_benchmark_rejected():
    db, engine = make_isolated_session()
    try:
        world = seed_benchmark_world(db)
        benchmark = Benchmark(
            grade_level=4,
            subject_id=world["subject"].id,
            tier1_min=80,
            tier2_min=70,
        )
        db.add(benchmark)
        db.flush()

        duplicate = Benchmark(
            grade_level=4,
            subject_id=world["subject"].id,
            tier1_min=85,
            tier2_min=75,
        )

        with pytest.raises(IntegrityError):
            db.add(duplicate)
            db.flush()
    finally:
        db.close()
        engine.dispose()


def test_invalid_thresholds_are_rejected_by_database_constraints():
    db, engine = make_isolated_session()
    try:
        world = seed_benchmark_world(db)
        benchmark = Benchmark(
            grade_level=4,
            subject_id=world["subject"].id,
            tier1_min=120,
            tier2_min=70,
        )

        with pytest.raises(IntegrityError):
            db.add(benchmark)
            db.flush()
    finally:
        db.close()
        engine.dispose()


def test_invalid_threshold_order_is_rejected_by_database_constraint():
    db, engine = make_isolated_session()
    try:
        world = seed_benchmark_world(db)
        benchmark = Benchmark(
            grade_level=4,
            subject_id=world["subject"].id,
            tier1_min=65,
            tier2_min=70,
        )

        with pytest.raises(IntegrityError):
            db.add(benchmark)
            db.flush()
    finally:
        db.close()
        engine.dispose()


@pytest.mark.parametrize("username", ["it_admin", "district_admin"])
def test_list_benchmarks_supports_grade_and_subject_filters(username, client, db):
    world = seed_benchmark_world(db)
    db.add_all(
        [
            Benchmark(grade_level=4, subject_id=world["subject"].id, tier1_min=82, tier2_min=72),
            Benchmark(grade_level=5, subject_id=world["subject"].id, tier1_min=81, tier2_min=71),
            Benchmark(grade_level=4, subject_id=world["reading"].id, tier1_min=80, tier2_min=70),
        ]
    )
    db.commit()

    login(client, username)
    response = client.get(f"/api/benchmarks?grade_level=4&subject_id={world['subject'].id}")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["grade_level"] == 4
    assert payload[0]["subject_id"] == str(world["subject"].id)


@pytest.mark.parametrize("username", ["principal", "teacher"])
def test_non_admin_roles_cannot_list_benchmarks(username, client, db):
    seed_benchmark_world(db)

    login(client, username)
    response = client.get("/api/benchmarks")

    assert response.status_code == 403


@pytest.mark.parametrize("username", ["it_admin", "district_admin"])
def test_post_benchmark_allows_admin_roles(username, client, db):
    world = seed_benchmark_world(db)
    login(client, username)

    response = client.post(
        "/api/benchmarks",
        json={
            "grade_level": 4,
            "subject_id": str(world["subject"].id),
            "tier1_min": 83,
            "tier2_min": 73,
        },
    )

    assert response.status_code == 201
    assert response.json()["tier1_min"] == 83


@pytest.mark.parametrize(
    ("username", "method", "path_suffix", "expected_status"),
    [
        ("principal", "post", "", 403),
        ("teacher", "post", "", 403),
        ("principal", "patch", "/{benchmark_id}", 403),
        ("teacher", "patch", "/{benchmark_id}", 403),
        ("principal", "delete", "/{benchmark_id}", 403),
        ("teacher", "delete", "/{benchmark_id}", 403),
    ],
)
def test_non_admin_roles_cannot_write_benchmarks(username, method, path_suffix, expected_status, client, db):
    world = seed_benchmark_world(db)
    benchmark = Benchmark(
        grade_level=4,
        subject_id=world["subject"].id,
        tier1_min=80,
        tier2_min=70,
    )
    db.add(benchmark)
    db.commit()
    db.refresh(benchmark)

    login(client, username)
    path = "/api/benchmarks" + path_suffix.format(benchmark_id=benchmark.id)
    if method == "post":
        response = client.post(
            path,
            json={"grade_level": 4, "subject_id": str(world["subject"].id), "tier1_min": 81, "tier2_min": 71},
        )
    elif method == "patch":
        response = client.patch(path, json={"tier1_min": 81})
    else:
        response = client.delete(path)

    assert response.status_code == expected_status


def test_patch_benchmark_updates_thresholds(client, db):
    world = seed_benchmark_world(db)
    benchmark = Benchmark(
        grade_level=4,
        subject_id=world["subject"].id,
        tier1_min=80,
        tier2_min=70,
    )
    db.add(benchmark)
    db.commit()
    db.refresh(benchmark)

    login(client, "it_admin")
    response = client.patch(f"/api/benchmarks/{benchmark.id}", json={"tier2_min": 68})

    assert response.status_code == 200
    assert response.json()["tier1_min"] == 80
    assert response.json()["tier2_min"] == 68


def test_patch_benchmark_merges_existing_thresholds_before_validation(client, db):
    world = seed_benchmark_world(db)
    benchmark = Benchmark(
        grade_level=4,
        subject_id=world["subject"].id,
        tier1_min=80,
        tier2_min=70,
    )
    db.add(benchmark)
    db.commit()
    db.refresh(benchmark)

    login(client, "district_admin")
    response = client.patch(f"/api/benchmarks/{benchmark.id}", json={"tier1_min": 65})

    assert response.status_code == 422
    db.refresh(benchmark)
    assert benchmark.tier1_min == 80
    assert benchmark.tier2_min == 70


def test_delete_benchmark_removes_override_and_restores_default_mtss_thresholds(client, db):
    world = seed_benchmark_world(db)
    benchmark = Benchmark(
        grade_level=4,
        subject_id=world["subject"].id,
        tier1_min=90,
        tier2_min=75,
    )
    db.add(benchmark)
    db.flush()

    from app.models import Score, ScoreType

    db.add(
        Score(
            student_id=world["student"].id,
            subject_id=world["subject"].id,
            score_type=ScoreType.quiz,
            value=72.0,
            date=date(2026, 4, 1),
        )
    )
    db.commit()
    db.refresh(benchmark)

    assert get_student_tier(db, world["student"].id, world["subject"].id).value == "tier3"

    login(client, "it_admin")
    response = client.delete(f"/api/benchmarks/{benchmark.id}")

    assert response.status_code == 204
    assert get_student_tier(db, world["student"].id, world["subject"].id).value == "tier2"

import uuid
from datetime import datetime, timezone
import shutil
from pathlib import Path

from alembic import command
from alembic.config import Config
import pytest
from sqlalchemy import create_engine, inspect, select
from sqlalchemy.exc import IntegrityError

from app.models import AIRec
from app.models.ai_rec import AITargetType
from app.models import Class, School, Student, User, UserRole
from app.schemas.ai import AIRecommendationResponse
from app.services.auth import hash_password


def seed_ai_context(db):
    school = School(name="Test School")
    db.add(school)
    db.flush()

    teacher = User(
        username="teacher",
        hashed_password=hash_password("password1"),
        role=UserRole.teacher,
        school_id=school.id,
    )
    db.add(teacher)
    db.flush()

    cls = Class(name="5A", grade_level=5, school_id=school.id, teacher_id=teacher.id)
    db.add(cls)
    db.flush()

    student = Student(
        name="Ada Lovelace",
        student_id_number="S001",
        grade_level=5,
        school_id=school.id,
        class_id=cls.id,
    )
    db.add(student)
    db.flush()

    return {"school": school, "teacher": teacher, "class": cls, "student": student}


def test_ai_recommendation_response_serializes_class_target(db):
    world = seed_ai_context(db)
    rec = AIRec(
        id=uuid.uuid4(),
        target_type=AITargetType.class_,
        student_id=None,
        class_id=world["class"].id,
        created_by=world["teacher"].id,
        model_name="llama3.2",
        temperature=0.7,
        prompt="prompt text",
        response="raw response",
        snapshot={
            "class": {"id": str(world["class"].id), "name": "5A"},
            "overall_average": 72.5,
            "recommended_tier": "tier2",
        },
        parse_error=None,
        created_at=datetime.now(timezone.utc),
    )

    payload = AIRecommendationResponse.model_validate(rec)

    assert payload.target_type == "class"
    assert payload.class_id == world["class"].id
    assert payload.created_by == world["teacher"].id
    assert payload.snapshot["recommended_tier"] == "tier2"
    assert payload.model_name == "llama3.2"


def test_ai_recommendation_response_serializes_student_target(db):
    world = seed_ai_context(db)
    rec = AIRec(
        id=uuid.uuid4(),
        target_type=AITargetType.student,
        student_id=world["student"].id,
        class_id=None,
        created_by=world["teacher"].id,
        model_name="llama3.2",
        temperature=0.7,
        prompt="prompt text",
        response="raw response",
        snapshot={
            "student": {"id": str(world["student"].id), "name": "Ada Lovelace"},
            "overall_average": 72.5,
            "recommended_tier": "tier2",
        },
        parse_error=None,
        created_at=datetime.now(timezone.utc),
    )

    payload = AIRecommendationResponse.model_validate(rec)

    assert payload.target_type == "student"
    assert payload.student_id == world["student"].id
    assert payload.created_by == world["teacher"].id
    assert payload.model_name == "llama3.2"


def test_ai_recommendation_persists_class_target_value(db):
    world = seed_ai_context(db)
    rec = AIRec(
        target_type=AITargetType.class_,
        student_id=None,
        class_id=world["class"].id,
        created_by=world["teacher"].id,
        model_name="llama3.2",
        temperature=0.7,
        prompt="prompt text",
        response="raw response",
        snapshot={
            "class": {"id": str(world["class"].id), "name": "5A"},
            "overall_average": 72.5,
            "recommended_tier": "tier2",
        },
        parse_error=None,
        created_at=datetime.now(timezone.utc),
    )
    db.add(rec)
    db.commit()

    raw_target_type = db.execute(
        select(AIRec.target_type).where(AIRec.id == rec.id)
    ).scalar_one()

    assert raw_target_type == "class"


def test_ai_recommendation_rejects_both_targets_populated(db):
    world = seed_ai_context(db)
    rec = AIRec(
        target_type=AITargetType.student,
        student_id=world["student"].id,
        class_id=world["class"].id,
        created_by=world["teacher"].id,
        model_name="llama3.2",
        temperature=0.7,
        prompt="prompt text",
        response="raw response",
        snapshot={},
        parse_error=None,
        created_at=datetime.now(timezone.utc),
    )

    with db.begin_nested():
        db.add(rec)
        with pytest.raises(IntegrityError):
            db.flush()


def test_ai_recommendation_rejects_missing_targets(db):
    world = seed_ai_context(db)
    rec = AIRec(
        target_type=AITargetType.student,
        student_id=None,
        class_id=None,
        created_by=world["teacher"].id,
        model_name="llama3.2",
        temperature=0.7,
        prompt="prompt text",
        response="raw response",
        snapshot={},
        parse_error=None,
        created_at=datetime.now(timezone.utc),
    )

    with db.begin_nested():
        db.add(rec)
        with pytest.raises(IntegrityError):
            db.flush()


def test_ai_migration_enforces_target_type_enum_constraint(monkeypatch):
    backend_root = Path(__file__).resolve().parents[2]
    temp_dir = Path.home() / ".codex" / "memories" / f"phase3a_ai_migration_{uuid.uuid4().hex}"
    temp_dir.mkdir()
    db_path = temp_dir / "ai_migration.sqlite3"
    database_url = f"sqlite:///{db_path.as_posix()}"

    monkeypatch.setattr("app.config.settings.database_url", database_url)

    config = Config()
    config.set_main_option("script_location", str(backend_root / "alembic"))
    config.set_main_option("sqlalchemy.url", database_url)

    command.upgrade(config, "ccb6db26e00c")

    engine = create_engine(database_url)
    try:
        inspector = inspect(engine)
        columns = {column["name"] for column in inspector.get_columns("ai_recs")}
        check_constraints = inspector.get_check_constraints("ai_recs")

        assert {
            "target_type",
            "student_id",
            "class_id",
            "created_by",
            "model_name",
            "temperature",
            "prompt",
            "response",
            "snapshot",
            "parse_error",
            "created_at",
        } <= columns
        assert any(
            constraint["name"] == "ck_ai_recs_target_consistency"
            for constraint in check_constraints
        )
        assert any(
            "target_type" in constraint["sqltext"]
            and "'student'" in constraint["sqltext"]
            and "'class'" in constraint["sqltext"]
            for constraint in check_constraints
        )
    finally:
        engine.dispose()
        shutil.rmtree(temp_dir, ignore_errors=True)

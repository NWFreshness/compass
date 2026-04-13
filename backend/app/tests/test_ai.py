import uuid
from datetime import date, datetime, timezone
import os
import tempfile
from pathlib import Path

from alembic import command
from alembic.config import Config
import httpx
import pytest
from sqlalchemy import create_engine, inspect, select
from sqlalchemy.exc import IntegrityError

from app.models import AIRec, Benchmark, Score, ScoreType, Subject
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


def seed_ai_world(db):
    world = seed_ai_context(db)

    math = Subject(name=f"Math {uuid.uuid4()}")
    reading = Subject(name=f"Reading {uuid.uuid4()}")
    db.add_all([math, reading])
    db.flush()

    db.add_all(
        [
            Benchmark(
                grade_level=world["student"].grade_level,
                subject_id=math.id,
                tier1_min=85.0,
                tier2_min=75.0,
            ),
            Benchmark(
                grade_level=world["student"].grade_level,
                subject_id=reading.id,
                tier1_min=90.0,
                tier2_min=80.0,
            ),
        ]
    )
    db.flush()

    db.add_all(
        [
            Score(
                student_id=world["student"].id,
                subject_id=math.id,
                score_type=ScoreType.quiz,
                value=74.0,
                date=date(2026, 4, 10),
            ),
            Score(
                student_id=world["student"].id,
                subject_id=math.id,
                score_type=ScoreType.test,
                value=76.0,
                date=date(2026, 4, 3),
            ),
            Score(
                student_id=world["student"].id,
                subject_id=reading.id,
                score_type=ScoreType.quiz,
                value=70.0,
                date=date(2026, 4, 12),
            ),
            Score(
                student_id=world["student"].id,
                subject_id=reading.id,
                score_type=ScoreType.homework,
                value=70.0,
                date=date(2026, 4, 1),
            ),
        ]
    )
    db.flush()

    world["subjects"] = {"math": math, "reading": reading}
    return world


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
    temp_root = Path.home() / ".codex" / "memories"
    temp_root.mkdir(parents=True, exist_ok=True)
    temp_file = tempfile.NamedTemporaryFile(dir=str(temp_root), suffix=".sqlite3", delete=False)
    temp_file.close()
    db_path = Path(temp_file.name)
    database_url = f"sqlite:///{db_path.as_posix()}"

    monkeypatch.setattr("app.config.settings.database_url", database_url)

    config = Config()
    config.set_main_option("script_location", str(backend_root / "alembic"))
    config.set_main_option("sqlalchemy.url", database_url)

    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            command.upgrade(config, "ccb6db26e00c")

            inspector = inspect(connection)
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
        if db_path.exists():
            os.unlink(db_path)


def test_build_student_snapshot_uses_benchmark_aware_tiers(db):
    from app.services.ai_analysis import build_student_snapshot

    world = seed_ai_world(db)

    snapshot = build_student_snapshot(db, world["student"].id)

    assert snapshot["student"] == {
        "id": str(world["student"].id),
        "name": "Ada Lovelace",
        "grade_level": 5,
    }
    assert snapshot["overall_average"] == 72.5
    assert snapshot["recommended_tier"] == "tier2"
    assert snapshot["subjects"] == [
        {
            "subject_id": str(world["subjects"]["math"].id),
            "subject_name": world["subjects"]["math"].name,
            "average": 75.0,
            "tier": "tier2",
        },
        {
            "subject_id": str(world["subjects"]["reading"].id),
            "subject_name": world["subjects"]["reading"].name,
            "average": 70.0,
            "tier": "tier3",
        },
    ]
    assert snapshot["recent_scores"] == [
        {
            "date": "2026-04-12",
            "subject": world["subjects"]["reading"].name,
            "score_type": "quiz",
            "value": 70.0,
        },
        {
            "date": "2026-04-10",
            "subject": world["subjects"]["math"].name,
            "score_type": "quiz",
            "value": 74.0,
        },
        {
            "date": "2026-04-03",
            "subject": world["subjects"]["math"].name,
            "score_type": "test",
            "value": 76.0,
        },
    ]


def test_parse_ai_response_extracts_structured_sections():
    from app.services.ai_analysis import parse_ai_response

    text = """Recommended MTSS Tier: Tier 2
Curriculum Recommendations:
- reteach fractions
- spiral review warmups
Intervention Strategies:
- small group work
- weekly progress monitoring
Rationale:
Average score is 72.5 with low quiz performance."""

    parsed = parse_ai_response(text)

    assert parsed == {
        "recommended_tier": "tier2",
        "curriculum_recommendations": [
            "reteach fractions",
            "spiral review warmups",
        ],
        "intervention_strategies": [
            "small group work",
            "weekly progress monitoring",
        ],
        "rationale": "Average score is 72.5 with low quiz performance.",
    }


def test_generate_text_raises_controlled_error_on_http_failure(monkeypatch):
    from app.services.ollama import OllamaError, generate_text

    def fake_post(*args, **kwargs):
        raise httpx.HTTPStatusError(
            "boom",
            request=httpx.Request("POST", "http://testserver/api/generate"),
            response=httpx.Response(500, request=httpx.Request("POST", "http://testserver/api/generate")),
        )

    monkeypatch.setattr("app.config.settings.ollama_url", "http://testserver")
    monkeypatch.setattr("app.config.settings.ollama_model", "llama3.2")
    monkeypatch.setattr("app.config.settings.ollama_temperature", 0.2)
    monkeypatch.setattr("app.config.settings.ollama_timeout_seconds", 12.5)
    monkeypatch.setattr("app.services.ollama.httpx.post", fake_post)

    with pytest.raises(OllamaError, match="Ollama request failed"):
        generate_text("Build a support plan.")

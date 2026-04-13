import pathlib
import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import AIRec, AITargetType, Class, School, Score, ScoreType, Student, Subject, User, UserRole
from app.schemas.ai import AIRecommendationResponse
from app.services.auth import hash_password


# ---------------------------------------------------------------------------
# Seed helpers
# ---------------------------------------------------------------------------

def seed_ai_context(db):
    """Minimal seed: one school, teacher, class, student, subject."""
    school = School(name="AI School")
    db.add(school)
    db.flush()
    teacher = User(
        username="teacher",
        hashed_password=hash_password("password1"),
        role=UserRole.teacher,
        school_id=school.id,
    )
    other_teacher = User(
        username="other_teacher",
        hashed_password=hash_password("password1"),
        role=UserRole.teacher,
        school_id=school.id,
    )
    principal = User(
        username="principal",
        hashed_password=hash_password("password1"),
        role=UserRole.principal,
        school_id=school.id,
    )
    db.add_all([teacher, other_teacher, principal])
    db.flush()
    cls = Class(name="5A", grade_level=5, school_id=school.id, teacher_id=teacher.id)
    db.add(cls)
    db.flush()
    student = Student(
        name="Ada Lovelace",
        student_id_number="S200",
        grade_level=5,
        school_id=school.id,
        class_id=cls.id,
    )
    subject = Subject(name="Math")
    db.add_all([student, subject])
    db.flush()
    return {
        "school": school,
        "teacher": teacher,
        "other_teacher": other_teacher,
        "principal": principal,
        "class": cls,
        "student": student,
        "subject": subject,
    }


def seed_ai_world(db):
    """Full seed with scores for service/snapshot tests."""
    world = seed_ai_context(db)
    scores = [
        Score(
            student_id=world["student"].id,
            subject_id=world["subject"].id,
            score_type=ScoreType.quiz,
            value=72.0,
            date=datetime(2026, 3, 1).date(),
        ),
        Score(
            student_id=world["student"].id,
            subject_id=world["subject"].id,
            score_type=ScoreType.test,
            value=73.0,
            date=datetime(2026, 3, 15).date(),
        ),
    ]
    db.add_all(scores)
    db.commit()
    return world


def create_ai_rec(db, *, student_id, created_at: str):
    """Helper to insert a history record with a specified created_at."""
    world_teacher = db.query(User).filter(User.username == "teacher").first()
    rec = AIRec(
        target_type=AITargetType.student,
        student_id=student_id,
        class_id=None,
        created_by=world_teacher.id,
        model_name="llama3.2",
        temperature=0.7,
        prompt="prompt",
        response="response",
        snapshot={"overall_average": 72.5},
        parse_error=None,
        created_at=datetime.fromisoformat(created_at),
    )
    db.add(rec)
    db.commit()
    return rec


FAKE_AI_RESPONSE = """\
Recommended MTSS Tier: Tier 2
Curriculum Recommendations:
- reteach fractions
Intervention Strategies:
- small group work
Rationale:
Average score is 72.5 with low quiz performance."""


# ---------------------------------------------------------------------------
# Task 1: Schema tests
# ---------------------------------------------------------------------------

def test_ai_recommendation_response_serializes_snapshot_fields():
    rec = AIRec(
        id=uuid.uuid4(),
        target_type=AITargetType.student,
        student_id=uuid.uuid4(),
        class_id=None,
        created_by=uuid.uuid4(),
        model_name="llama3.2",
        temperature=0.7,
        prompt="prompt text",
        response="raw response",
        snapshot={
            "student": {"id": "s1", "name": "Ada"},
            "overall_average": 72.5,
            "recommended_tier": "tier2",
        },
        parse_error=None,
        created_at=datetime.now(timezone.utc),
    )

    payload = AIRecommendationResponse.model_validate(rec)

    assert payload.target_type == "student"
    assert payload.created_by == rec.created_by
    assert payload.model_name == "llama3.2"
    assert payload.snapshot["recommended_tier"] == "tier2"


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
        snapshot={"class": {"id": str(world["class"].id), "name": "5A"}, "recommended_tier": "tier2"},
        parse_error=None,
        created_at=datetime.now(timezone.utc),
    )

    payload = AIRecommendationResponse.model_validate(rec)

    assert payload.target_type == "class"
    assert payload.class_id == world["class"].id
    assert payload.created_by == world["teacher"].id


def test_ai_migration_declares_target_type_constraint():
    migration_text = pathlib.Path(__file__).parent.parent.parent.joinpath(
        "alembic/versions/ccb6db26e00c_initial_schema.py"
    ).read_text(encoding="utf-8")

    assert "create_constraint=True" in migration_text


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

    with pytest.raises(IntegrityError):
        db.add(rec)
        db.flush()


# ---------------------------------------------------------------------------
# Task 2: Service tests
# ---------------------------------------------------------------------------

def test_build_student_snapshot_uses_benchmark_aware_tiers(db):
    from app.services.ai_analysis import build_student_snapshot

    world = seed_ai_world(db)

    snapshot = build_student_snapshot(db, world["student"].id)

    assert snapshot["student"]["name"] == "Ada Lovelace"
    assert snapshot["overall_average"] == 72.5
    assert snapshot["recommended_tier"] == "tier2"
    assert snapshot["subjects"][0]["tier"] in {"tier1", "tier2", "tier3"}


def test_parse_ai_response_extracts_structured_sections():
    from app.services.ai_analysis import parse_ai_response

    parsed = parse_ai_response(FAKE_AI_RESPONSE)

    assert parsed["recommended_tier"] == "tier2"
    assert "reteach fractions" in parsed["curriculum_recommendations"]
    assert "small group work" in parsed["intervention_strategies"]


# ---------------------------------------------------------------------------
# Task 3: Route tests
# ---------------------------------------------------------------------------

def test_student_ai_analysis_creates_history_entry(client, db, monkeypatch):
    world = seed_ai_world(db)
    monkeypatch.setattr("app.services.ollama.generate_text", lambda prompt: FAKE_AI_RESPONSE)

    assert client.post("/api/auth/login", json={"username": "teacher", "password": "password1"}).status_code == 200
    response = client.post(f"/api/ai/student/{world['student'].id}/analyze")

    assert response.status_code == 201
    payload = response.json()
    assert payload["target_type"] == "student"
    assert payload["snapshot"]["student"]["name"] == "Ada Lovelace"


def test_teacher_cannot_analyze_unassigned_class(client, db, monkeypatch):
    world = seed_ai_world(db)
    monkeypatch.setattr("app.services.ollama.generate_text", lambda prompt: FAKE_AI_RESPONSE)

    assert client.post("/api/auth/login", json={"username": "other_teacher", "password": "password1"}).status_code == 200
    response = client.post(f"/api/ai/class/{world['class'].id}/analyze")

    assert response.status_code == 403


def test_student_history_is_newest_first(client, db):
    world = seed_ai_world(db)
    create_ai_rec(db, student_id=world["student"].id, created_at="2026-04-01T00:00:00+00:00")
    create_ai_rec(db, student_id=world["student"].id, created_at="2026-04-02T00:00:00+00:00")

    assert client.post("/api/auth/login", json={"username": "principal", "password": "password1"}).status_code == 200
    response = client.get(f"/api/ai/student/{world['student'].id}/history")

    assert response.status_code == 200
    items = response.json()
    assert len(items) >= 2
    assert items[0]["created_at"] > items[1]["created_at"]


def test_class_ai_analysis_creates_history_entry(client, db, monkeypatch):
    world = seed_ai_world(db)
    monkeypatch.setattr("app.services.ollama.generate_text", lambda prompt: FAKE_AI_RESPONSE)

    assert client.post("/api/auth/login", json={"username": "teacher", "password": "password1"}).status_code == 200
    response = client.post(f"/api/ai/class/{world['class'].id}/analyze")

    assert response.status_code == 201
    payload = response.json()
    assert payload["target_type"] == "class"


def test_class_history_returns_newest_first(client, db):
    world = seed_ai_world(db)
    # Insert two class-level history records directly
    for ts in ["2026-04-01T00:00:00+00:00", "2026-04-02T00:00:00+00:00"]:
        teacher = db.query(User).filter(User.username == "teacher").first()
        rec = AIRec(
            target_type=AITargetType.class_,
            student_id=None,
            class_id=world["class"].id,
            created_by=teacher.id,
            model_name="llama3.2",
            temperature=0.7,
            prompt="p",
            response="r",
            snapshot={},
            parse_error=None,
            created_at=datetime.fromisoformat(ts),
        )
        db.add(rec)
    db.commit()

    assert client.post("/api/auth/login", json={"username": "teacher", "password": "password1"}).status_code == 200
    response = client.get(f"/api/ai/class/{world['class'].id}/history")

    assert response.status_code == 200
    items = response.json()
    assert len(items) >= 2
    assert items[0]["created_at"] > items[1]["created_at"]

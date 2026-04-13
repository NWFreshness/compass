import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.models import AIRec
from app.models.ai_rec import AITargetType
from app.models import Class, School, User, UserRole
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

    return {"school": school, "teacher": teacher, "class": cls}


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
    assert payload.snapshot["recommended_tier"] == "tier2"


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
        text("select target_type from ai_recs where id = :id"),
        {"id": rec.id.hex},
    ).scalar_one()

    assert raw_target_type == "class"


def test_ai_recommendation_rejects_both_targets_populated(db):
    world = seed_ai_context(db)
    rec = AIRec(
        target_type=AITargetType.student,
        student_id=uuid.uuid4(),
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

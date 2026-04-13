import uuid
from datetime import datetime, timezone

from app.models import AIRec
from app.schemas.ai import AIRecommendationResponse


def test_ai_recommendation_response_serializes_snapshot_fields():
    rec = AIRec(
        id=uuid.uuid4(),
        target_type="student",
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
    assert payload.model_name == "llama3.2"
    assert payload.snapshot["recommended_tier"] == "tier2"

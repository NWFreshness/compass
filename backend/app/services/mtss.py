import enum
from sqlalchemy.orm import Session
from app.models import Score, Benchmark, Student


class TierResult(str, enum.Enum):
    tier1 = "tier1"
    tier2 = "tier2"
    tier3 = "tier3"


def calculate_tier(avg_score: float, tier1_min: float = 80.0, tier2_min: float = 70.0) -> TierResult:
    if avg_score >= tier1_min:
        return TierResult.tier1
    if avg_score >= tier2_min:
        return TierResult.tier2
    return TierResult.tier3


def get_student_tier(db: Session, student_id, subject_id=None) -> TierResult | None:
    """Compute MTSS tier for a student, optionally filtered by subject."""
    query = db.query(Score).filter(Score.student_id == student_id)
    if subject_id:
        query = query.filter(Score.subject_id == subject_id)
    scores = query.all()
    if not scores:
        return None
    avg = sum(s.value for s in scores) / len(scores)

    student = db.query(Student).filter(Student.id == student_id).first()
    benchmark = None
    if student and subject_id:
        benchmark = (
            db.query(Benchmark)
            .filter(Benchmark.grade_level == student.grade_level, Benchmark.subject_id == subject_id)
            .first()
        )
    tier1_min = benchmark.tier1_min if benchmark else 80.0
    tier2_min = benchmark.tier2_min if benchmark else 70.0
    return calculate_tier(avg, tier1_min, tier2_min)

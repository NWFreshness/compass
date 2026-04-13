from sqlalchemy.orm import Session
from app.models import Class, Score, Student
from app.services.mtss import calculate_tier


def get_class_summary(db: Session, class_id) -> dict:
    """Return student count, avg score, and tier distribution for a class."""
    students = db.query(Student).filter(Student.class_id == class_id).all()
    if not students:
        return {
            "student_count": 0,
            "avg_score": None,
            "tier_distribution": {"tier1": 0, "tier2": 0, "tier3": 0},
        }

    tier_counts = {"tier1": 0, "tier2": 0, "tier3": 0}
    all_scores = []
    for student in students:
        scores = db.query(Score).filter(Score.student_id == student.id).all()
        if scores:
            avg = sum(s.value for s in scores) / len(scores)
            all_scores.append(avg)
            tier = calculate_tier(avg)
            tier_counts[tier.value] += 1

    return {
        "student_count": len(students),
        "avg_score": sum(all_scores) / len(all_scores) if all_scores else None,
        "tier_distribution": tier_counts,
    }


def get_at_risk_students(db: Session, class_ids: list) -> list[dict]:
    """Return Tier 2 and Tier 3 students across the given classes."""
    result = []
    for class_id in class_ids:
        cls = db.query(Class).filter(Class.id == class_id).first()
        if not cls:
            continue
        students = db.query(Student).filter(Student.class_id == class_id).all()
        for student in students:
            scores = db.query(Score).filter(Score.student_id == student.id).all()
            if not scores:
                continue
            avg = sum(s.value for s in scores) / len(scores)
            tier = calculate_tier(avg)
            if tier.value in ("tier2", "tier3"):
                result.append({
                    "student_id": student.id,
                    "student_name": student.name,
                    "class_name": cls.name,
                    "avg_score": avg,
                    "tier": tier.value,
                })
    return result


def get_grade_averages(db: Session, school_id) -> list[dict]:
    """Return avg score per grade level for a school."""
    students = db.query(Student).filter(Student.school_id == school_id).all()
    grade_data: dict[int, list[float]] = {}
    for student in students:
        scores = db.query(Score).filter(Score.student_id == student.id).all()
        if scores:
            avg = sum(s.value for s in scores) / len(scores)
            grade_data.setdefault(student.grade_level, []).append(avg)

    return [
        {
            "grade_level": grade,
            "avg_score": sum(avgs) / len(avgs),
            "student_count": len(avgs),
        }
        for grade, avgs in sorted(grade_data.items())
    ]


def get_school_summary(db: Session, school_id) -> dict:
    """Return school-level summary including high_risk flag."""
    classes = db.query(Class).filter(Class.school_id == school_id).all()
    class_ids = [c.id for c in classes]

    total = 0
    tier_counts = {"tier1": 0, "tier2": 0, "tier3": 0}
    all_avgs = []

    for class_id in class_ids:
        summary = get_class_summary(db, class_id)
        total += summary["student_count"]
        for tier, count in summary["tier_distribution"].items():
            tier_counts[tier] += count
        if summary["avg_score"] is not None:
            all_avgs.append(summary["avg_score"])

    tier3_pct = tier_counts["tier3"] / total if total > 0 else 0.0

    return {
        "student_count": total,
        "avg_score": sum(all_avgs) / len(all_avgs) if all_avgs else None,
        "tier_distribution": tier_counts,
        "high_risk": tier3_pct > 0.30,
    }

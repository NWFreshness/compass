from collections import defaultdict
from sqlalchemy.orm import Session
from app.models import Class, Score, Student
from app.services.mtss import calculate_tier


def _scores_by_student(db: Session, student_ids: list) -> dict:
    """Return {student_id: [score_values]} for all given student IDs in one query."""
    if not student_ids:
        return {}
    rows = db.query(Score.student_id, Score.value).filter(Score.student_id.in_(student_ids)).all()
    result: dict = defaultdict(list)
    for student_id, value in rows:
        result[student_id].append(value)
    return result


def get_class_summary(db: Session, class_id) -> dict:
    students = db.query(Student).filter(Student.class_id == class_id).all()
    if not students:
        return {
            "student_count": 0,
            "avg_score": None,
            "tier_distribution": {"tier1": 0, "tier2": 0, "tier3": 0},
        }
    scores_map = _scores_by_student(db, [s.id for s in students])
    tier_counts = {"tier1": 0, "tier2": 0, "tier3": 0}
    student_avgs = []
    for student in students:
        vals = scores_map.get(student.id, [])
        if vals:
            avg = sum(vals) / len(vals)
            student_avgs.append(avg)
            tier_counts[calculate_tier(avg).value] += 1
    return {
        "student_count": len(students),
        "avg_score": sum(student_avgs) / len(student_avgs) if student_avgs else None,
        "tier_distribution": tier_counts,
    }


def get_at_risk_students(db: Session, class_ids: list) -> list[dict]:
    if not class_ids:
        return []
    classes = {c.id: c for c in db.query(Class).filter(Class.id.in_(class_ids)).all()}
    students = db.query(Student).filter(Student.class_id.in_(class_ids)).all()
    scores_map = _scores_by_student(db, [s.id for s in students])
    result = []
    for student in students:
        vals = scores_map.get(student.id, [])
        if not vals:
            continue
        avg = sum(vals) / len(vals)
        tier = calculate_tier(avg)
        if tier.value in ("tier2", "tier3"):
            cls = classes.get(student.class_id)
            result.append({
                "student_id": student.id,
                "student_name": student.name,
                "class_name": cls.name if cls else "",
                "avg_score": avg,
                "tier": tier.value,
            })
    return result


def get_grade_averages(db: Session, school_id) -> list[dict]:
    students = db.query(Student).filter(Student.school_id == school_id).all()
    if not students:
        return []
    scores_map = _scores_by_student(db, [s.id for s in students])
    grade_avgs: dict[int, list[float]] = defaultdict(list)
    for student in students:
        vals = scores_map.get(student.id, [])
        if vals:
            grade_avgs[student.grade_level].append(sum(vals) / len(vals))
    return [
        {
            "grade_level": grade,
            "avg_score": sum(avgs) / len(avgs),
            "student_count": len(avgs),
        }
        for grade, avgs in sorted(grade_avgs.items())
    ]


def get_school_summary(db: Session, school_id) -> dict:
    classes = db.query(Class).filter(Class.school_id == school_id).all()
    if not classes:
        return {
            "student_count": 0,
            "avg_score": None,
            "tier_distribution": {"tier1": 0, "tier2": 0, "tier3": 0},
            "high_risk": False,
        }
    # Load all students and scores in two queries
    class_ids = [c.id for c in classes]
    students = db.query(Student).filter(Student.class_id.in_(class_ids)).all()
    scores_map = _scores_by_student(db, [s.id for s in students])

    tier_counts = {"tier1": 0, "tier2": 0, "tier3": 0}
    all_student_avgs = []
    for student in students:
        vals = scores_map.get(student.id, [])
        if vals:
            avg = sum(vals) / len(vals)
            all_student_avgs.append(avg)
            tier_counts[calculate_tier(avg).value] += 1

    total = len(students)
    tier3_pct = tier_counts["tier3"] / total if total > 0 else 0.0
    return {
        "student_count": total,
        "avg_score": sum(all_student_avgs) / len(all_student_avgs) if all_student_avgs else None,
        "tier_distribution": tier_counts,
        "high_risk": tier3_pct > 0.30,
    }

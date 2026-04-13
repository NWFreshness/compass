import uuid
from collections import defaultdict

from sqlalchemy.orm import Session

from app.models import Score, Student
from app.services.mtss import calculate_tier, get_student_tier


def build_student_snapshot(db: Session, student_id: uuid.UUID) -> dict:
    student = db.query(Student).filter(Student.id == student_id).first()
    if student is None:
        raise ValueError("Student not found")

    scores = (
        db.query(Score)
        .filter(Score.student_id == student_id)
        .order_by(Score.date.desc(), Score.id.desc())
        .all()
    )
    if not scores:
        raise ValueError("Student has no scores")

    overall_average = round(sum(score.value for score in scores) / len(scores), 1)

    scores_by_subject: dict[uuid.UUID, list[Score]] = defaultdict(list)
    for score in scores:
        scores_by_subject[score.subject_id].append(score)

    subjects = []
    for subject_scores in sorted(
        scores_by_subject.values(),
        key=lambda items: items[0].subject.name.lower(),
    ):
        subject = subject_scores[0].subject
        average = round(sum(score.value for score in subject_scores) / len(subject_scores), 1)
        tier = get_student_tier(db, student_id, subject.id)
        subjects.append(
            {
                "subject_id": str(subject.id),
                "subject_name": subject.name,
                "average": average,
                "tier": tier.value if tier else None,
            }
        )

    recent_scores = [
        {
            "date": score.date.isoformat(),
            "subject": score.subject.name,
            "score_type": score.score_type.value,
            "value": score.value,
        }
        for score in scores[:3]
    ]

    return {
        "student": {
            "id": str(student.id),
            "name": student.name,
            "grade_level": student.grade_level,
        },
        "overall_average": overall_average,
        "recommended_tier": calculate_tier(overall_average).value,
        "subjects": subjects,
        "recent_scores": recent_scores,
    }


def build_student_prompt(snapshot: dict) -> str:
    lines = [
        "You are an MTSS recommendation assistant.",
        f"Student: {snapshot['student']['name']} (Grade {snapshot['student']['grade_level']})",
        f"Overall average: {snapshot['overall_average']}",
        f"Suggested baseline tier: {snapshot['recommended_tier']}",
        "Subject performance:",
    ]
    for subject in snapshot["subjects"]:
        lines.append(
            f"- {subject['subject_name']}: average {subject['average']}, tier {subject['tier']}"
        )
    lines.append("Recent scores:")
    for score in snapshot["recent_scores"]:
        lines.append(
            f"- {score['date']} {score['subject']} {score['score_type']}: {score['value']}"
        )
    lines.append("Respond with sections for Recommended MTSS Tier, Curriculum Recommendations, Intervention Strategies, and Rationale.")
    return "\n".join(lines)


def parse_ai_response(text: str) -> dict:
    result = {
        "recommended_tier": None,
        "curriculum_recommendations": [],
        "intervention_strategies": [],
        "rationale": "",
    }
    section = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        lowered = line.lower()
        if lowered.startswith("recommended mtss tier:"):
            tier_text = line.split(":", 1)[1].strip().lower().replace(" ", "")
            result["recommended_tier"] = tier_text.replace("tier", "tier")
            section = None
            continue
        if lowered == "curriculum recommendations:":
            section = "curriculum_recommendations"
            continue
        if lowered == "intervention strategies:":
            section = "intervention_strategies"
            continue
        if lowered == "rationale:":
            section = "rationale"
            continue

        if line.startswith("- ") and section in {
            "curriculum_recommendations",
            "intervention_strategies",
        }:
            result[section].append(line[2:].strip())
            continue

        if section == "rationale":
            result["rationale"] = (
                f"{result['rationale']} {line}".strip()
                if result["rationale"]
                else line
            )

    return result

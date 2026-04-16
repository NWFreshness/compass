import uuid
from collections.abc import Iterator
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.models import AIRec, AITargetType, Class, Score, Student, Subject
from app.services import ollama as ollama_client
from app.services.ollama import OllamaError
from app.services.mtss import calculate_tier, get_student_tier


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def parse_ai_response(text: str) -> dict:
    """Extract structured fields from a free-text Ollama response."""
    import re

    lines = [line.strip() for line in text.splitlines() if line.strip()]

    def _strip_md(line: str) -> str:
        """Remove leading/trailing markdown bold markers (**) and header markers (#)."""
        return re.sub(r"^\*+|^\#+|\*+$", "", line).strip()

    def _find(prefix: str) -> str | None:
        for line in lines:
            cleaned = _strip_md(line)
            if cleaned.lower().startswith(prefix.lower()):
                return cleaned.split(":", 1)[1].strip().strip("*").strip()
        return None

    raw_tier = _find("Recommended MTSS Tier:")
    recommended_tier = None
    if raw_tier:
        recommended_tier = raw_tier.lower().replace(" ", "")
        if recommended_tier not in {"tier1", "tier2", "tier3"}:
            recommended_tier = None

    bullet_lines = [
        re.sub(r"^[-*]\s+", "", line).strip()
        for line in lines
        if re.match(r"^[-*]\s+", line)
    ]
    curriculum = bullet_lines[:1]
    interventions = bullet_lines[1:2]

    rationale = next(
        (line for line in lines if "average score" in line.lower()),
        "",
    )

    return {
        "recommended_tier": recommended_tier,
        "curriculum_recommendations": curriculum,
        "intervention_strategies": interventions,
        "rationale": rationale,
    }


# ---------------------------------------------------------------------------
# Snapshot builders
# ---------------------------------------------------------------------------

def build_student_snapshot(db: Session, student_id: uuid.UUID) -> dict:
    """Build deterministic analysis inputs for a single student."""
    student = db.query(Student).filter(Student.id == student_id).first()
    scores = (
        db.query(Score)
        .filter(Score.student_id == student_id)
        .order_by(Score.date.desc())
        .all()
    )
    if not scores:
        overall_average = 0.0
    else:
        overall_average = round(sum(s.value for s in scores) / len(scores), 1)

    subject_rows = []
    for subject_id in sorted({str(s.subject_id) for s in scores}):
        subject_id_uuid = uuid.UUID(subject_id)
        subject = db.query(Subject).filter(Subject.id == subject_id_uuid).first()
        subject_name = subject.name if subject else subject_id
        tier = get_student_tier(db, student_id, subject_id_uuid)
        subj_scores = [s for s in scores if s.subject_id == subject_id_uuid]
        avg = round(sum(s.value for s in subj_scores) / len(subj_scores), 1)
        subject_rows.append({
            "subject_id": subject_id,
            "subject_name": subject_name,
            "average": avg,
            "tier": tier.value if tier else "tier1",
        })

    return {
        "student": {
            "id": str(student.id),
            "name": student.name,
            "grade_level": student.grade_level,
        },
        "overall_average": overall_average,
        "recommended_tier": calculate_tier(overall_average).value,
        "subjects": subject_rows,
        "recent_scores": [
            {"date": s.date.isoformat(), "value": s.value}
            for s in scores[:5]
        ],
    }


def build_class_snapshot(db: Session, class_id: uuid.UUID) -> dict:
    """Build deterministic analysis inputs for a class."""
    cls = db.query(Class).filter(Class.id == class_id).first()
    students = db.query(Student).filter(Student.class_id == class_id).all()

    student_summaries = []
    all_scores = []
    for student in students:
        scores = db.query(Score).filter(Score.student_id == student.id).all()
        all_scores.extend(scores)
        if scores:
            avg = round(sum(s.value for s in scores) / len(scores), 1)
            tier = calculate_tier(avg)
            student_summaries.append({
                "student_id": str(student.id),
                "name": student.name,
                "average": avg,
                "tier": tier.value,
            })

    class_avg = 0.0
    if all_scores:
        class_avg = round(sum(s.value for s in all_scores) / len(all_scores), 1)

    tier_counts = {"tier1": 0, "tier2": 0, "tier3": 0}
    for s in student_summaries:
        tier_counts[s["tier"]] = tier_counts.get(s["tier"], 0) + 1

    return {
        "class": {
            "id": str(cls.id),
            "name": cls.name,
            "grade_level": cls.grade_level,
        },
        "overall_average": class_avg,
        "recommended_tier": calculate_tier(class_avg).value,
        "tier_distribution": tier_counts,
        "students": student_summaries,
    }


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------

def _build_student_prompt(snapshot: dict) -> str:
    s = snapshot["student"]
    subjects = "\n".join(
        f"  - {row['subject_name']}: avg {row['average']} ({row['tier']})"
        for row in snapshot["subjects"]
    )
    recent = ", ".join(str(r["value"]) for r in snapshot["recent_scores"])
    return (
        f"You are an educational support specialist. Analyze the following student performance data "
        f"and provide targeted MTSS recommendations.\n\n"
        f"Student: {s['name']}, Grade {s['grade_level']}\n"
        f"Overall average: {snapshot['overall_average']}\n"
        f"Current tier: {snapshot['recommended_tier']}\n"
        f"Subject performance:\n{subjects}\n"
        f"Recent scores: {recent}\n\n"
        f"Please respond with exactly these sections:\n"
        f"Recommended MTSS Tier: (Tier 1, Tier 2, or Tier 3)\n"
        f"Curriculum Recommendations:\n- (list)\n"
        f"Intervention Strategies:\n- (list)\n"
        f"Rationale:\n(brief explanation referencing the score data above)"
    )


def _build_class_prompt(snapshot: dict) -> str:
    c = snapshot["class"]
    dist = snapshot["tier_distribution"]
    return (
        f"You are an educational support specialist. Analyze the following class performance data "
        f"and provide targeted MTSS recommendations.\n\n"
        f"Class: {c['name']}, Grade {c['grade_level']}\n"
        f"Class average: {snapshot['overall_average']}\n"
        f"Overall tier: {snapshot['recommended_tier']}\n"
        f"Tier distribution: Tier 1: {dist.get('tier1', 0)}, Tier 2: {dist.get('tier2', 0)}, "
        f"Tier 3: {dist.get('tier3', 0)}\n\n"
        f"Please respond with exactly these sections:\n"
        f"Recommended MTSS Tier: (Tier 1, Tier 2, or Tier 3)\n"
        f"Curriculum Recommendations:\n- (list)\n"
        f"Intervention Strategies:\n- (list)\n"
        f"Rationale:\n(brief explanation referencing the class data above)"
    )


# ---------------------------------------------------------------------------
# Main analysis functions
# ---------------------------------------------------------------------------

def analyze_student(db: Session, *, student_id: uuid.UUID, created_by: uuid.UUID) -> AIRec:
    snapshot = build_student_snapshot(db, student_id)
    prompt = _build_student_prompt(snapshot)
    raw_response = ollama_client.generate_text(prompt)

    parsed = parse_ai_response(raw_response)
    parse_error = None if parsed.get("recommended_tier") else "Could not parse structured response"

    rec = AIRec(
        target_type=AITargetType.student,
        student_id=student_id,
        class_id=None,
        created_by=created_by,
        model_name=settings.ollama_model,
        temperature=settings.ollama_temperature,
        prompt=prompt,
        response=raw_response,
        snapshot=snapshot,
        parse_error=parse_error,
        created_at=datetime.now(timezone.utc),
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec


def analyze_class(db: Session, *, class_id: uuid.UUID, created_by: uuid.UUID) -> AIRec:
    snapshot = build_class_snapshot(db, class_id)
    prompt = _build_class_prompt(snapshot)
    raw_response = ollama_client.generate_text(prompt)

    parsed = parse_ai_response(raw_response)
    parse_error = None if parsed.get("recommended_tier") else "Could not parse structured response"

    rec = AIRec(
        target_type=AITargetType.class_,
        student_id=None,
        class_id=class_id,
        created_by=created_by,
        model_name=settings.ollama_model,
        temperature=settings.ollama_temperature,
        prompt=prompt,
        response=raw_response,
        snapshot=snapshot,
        parse_error=parse_error,
        created_at=datetime.now(timezone.utc),
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec


def analyze_student_stream(
    db: Session, *, student_id: uuid.UUID, created_by: uuid.UUID
) -> Iterator[str]:
    """Yield Ollama tokens for a student analysis, then save AIRec and yield done sentinel."""
    snapshot = build_student_snapshot(db, student_id)
    prompt = _build_student_prompt(snapshot)
    full_response = ""
    try:
        for token in ollama_client.generate_stream(prompt):
            full_response += token
            yield token
    except OllamaError as exc:
        yield f"\n__ERROR__:{exc}"
        return

    parsed = parse_ai_response(full_response)
    parse_error = None if parsed.get("recommended_tier") else "Could not parse structured response"
    rec = AIRec(
        target_type=AITargetType.student,
        student_id=student_id,
        class_id=None,
        created_by=created_by,
        model_name=settings.ollama_model,
        temperature=settings.ollama_temperature,
        prompt=prompt,
        response=full_response,
        snapshot=snapshot,
        parse_error=parse_error,
        created_at=datetime.now(timezone.utc),
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    yield f"\n__DONE__:{rec.id}"


def analyze_class_stream(
    db: Session, *, class_id: uuid.UUID, created_by: uuid.UUID
) -> Iterator[str]:
    """Yield Ollama tokens for a class analysis, then save AIRec and yield done sentinel."""
    snapshot = build_class_snapshot(db, class_id)
    prompt = _build_class_prompt(snapshot)
    full_response = ""
    try:
        for token in ollama_client.generate_stream(prompt):
            full_response += token
            yield token
    except OllamaError as exc:
        yield f"\n__ERROR__:{exc}"
        return

    parsed = parse_ai_response(full_response)
    parse_error = None if parsed.get("recommended_tier") else "Could not parse structured response"
    rec = AIRec(
        target_type=AITargetType.class_,
        student_id=None,
        class_id=class_id,
        created_by=created_by,
        model_name=settings.ollama_model,
        temperature=settings.ollama_temperature,
        prompt=prompt,
        response=full_response,
        snapshot=snapshot,
        parse_error=parse_error,
        created_at=datetime.now(timezone.utc),
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    yield f"\n__DONE__:{rec.id}"


def list_student_history(db: Session, student_id: uuid.UUID) -> list[AIRec]:
    return (
        db.query(AIRec)
        .filter(AIRec.student_id == student_id)
        .order_by(AIRec.created_at.desc())
        .all()
    )


def list_class_history(db: Session, class_id: uuid.UUID) -> list[AIRec]:
    return (
        db.query(AIRec)
        .filter(AIRec.class_id == class_id)
        .order_by(AIRec.created_at.desc())
        .all()
    )

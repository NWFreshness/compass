import pytest
from app.services.auth import hash_password
from app.models import User, UserRole, School, Class, Student, Subject, Score, ScoreType
from app.services.dashboard import get_class_summary, get_at_risk_students, get_grade_averages, get_school_summary
from datetime import date

# Helper: create a student with a known average score
def make_student_with_scores(db, name, sid, grade, school_id, class_id, subject_id, scores):
    student = Student(name=name, student_id_number=sid, grade_level=grade, school_id=school_id, class_id=class_id)
    db.add(student)
    db.flush()
    for i, val in enumerate(scores):
        db.add(Score(student_id=student.id, subject_id=subject_id, score_type=ScoreType.test, value=val, date=date(2026, 1, i+1)))
    db.flush()
    return student

def seed_base(db):
    school = School(name="Lincoln", address="123 Main")
    db.add(school)
    subject = Subject(name="Math")
    db.add(subject)
    teacher = User(username="teacher1", hashed_password=hash_password("x"), role=UserRole.teacher, school_id=None)
    db.add(teacher)
    db.flush()
    cls = Class(name="Grade 3A", grade_level=3, school_id=school.id, teacher_id=teacher.id)
    db.add(cls)
    db.flush()
    return school, subject, teacher, cls

def test_class_summary_empty(db):
    school, subject, teacher, cls = seed_base(db)
    summary = get_class_summary(db, cls.id)
    assert summary["student_count"] == 0
    assert summary["avg_score"] is None
    assert summary["tier_distribution"] == {"tier1": 0, "tier2": 0, "tier3": 0}

def test_class_summary_with_scores(db):
    school, subject, teacher, cls = seed_base(db)
    # tier1 student: avg 90
    make_student_with_scores(db, "Alice", "S001", 3, school.id, cls.id, subject.id, [90, 90])
    # tier2 student: avg 75
    make_student_with_scores(db, "Bob", "S002", 3, school.id, cls.id, subject.id, [75, 75])
    # tier3 student: avg 60
    make_student_with_scores(db, "Carol", "S003", 3, school.id, cls.id, subject.id, [60, 60])
    db.commit()

    summary = get_class_summary(db, cls.id)
    assert summary["student_count"] == 3
    assert summary["tier_distribution"] == {"tier1": 1, "tier2": 1, "tier3": 1}
    assert summary["avg_score"] == pytest.approx(75.0, abs=0.1)

def test_at_risk_excludes_tier1(db):
    school, subject, teacher, cls = seed_base(db)
    make_student_with_scores(db, "Alice", "S001", 3, school.id, cls.id, subject.id, [90])
    make_student_with_scores(db, "Bob", "S002", 3, school.id, cls.id, subject.id, [75])
    make_student_with_scores(db, "Carol", "S003", 3, school.id, cls.id, subject.id, [60])
    db.commit()

    at_risk = get_at_risk_students(db, [cls.id])
    names = [s["student_name"] for s in at_risk]
    assert "Alice" not in names
    assert "Bob" in names
    assert "Carol" in names

def test_at_risk_tiers_correct(db):
    school, subject, teacher, cls = seed_base(db)
    make_student_with_scores(db, "Bob", "S002", 3, school.id, cls.id, subject.id, [75])
    make_student_with_scores(db, "Carol", "S003", 3, school.id, cls.id, subject.id, [60])
    db.commit()

    at_risk = get_at_risk_students(db, [cls.id])
    tiers = {s["student_name"]: s["tier"] for s in at_risk}
    assert tiers["Bob"] == "tier2"
    assert tiers["Carol"] == "tier3"

def test_grade_averages(db):
    school, subject, teacher, cls = seed_base(db)
    make_student_with_scores(db, "Alice", "S001", 3, school.id, cls.id, subject.id, [80, 90])
    db.commit()

    avgs = get_grade_averages(db, school.id)
    assert len(avgs) == 1
    assert avgs[0]["grade_level"] == 3
    assert avgs[0]["avg_score"] == pytest.approx(85.0, abs=0.1)
    assert avgs[0]["student_count"] == 1

def test_school_summary_high_risk(db):
    school, subject, teacher, cls = seed_base(db)
    # 1 tier1, 2 tier3 → tier3 is 66% → high_risk
    make_student_with_scores(db, "Alice", "S001", 3, school.id, cls.id, subject.id, [90])
    make_student_with_scores(db, "Bob", "S002", 3, school.id, cls.id, subject.id, [60])
    make_student_with_scores(db, "Carol", "S003", 3, school.id, cls.id, subject.id, [60])
    db.commit()

    summary = get_school_summary(db, school.id)
    assert summary["high_risk"] is True

def test_school_summary_not_high_risk(db):
    school, subject, teacher, cls = seed_base(db)
    # 3 tier1, 1 tier3 → tier3 is 25% → not high_risk
    for i in range(3):
        make_student_with_scores(db, f"S{i}", f"ID{i}", 3, school.id, cls.id, subject.id, [90])
    make_student_with_scores(db, "Carol", "S003", 3, school.id, cls.id, subject.id, [60])
    db.commit()

    summary = get_school_summary(db, school.id)
    assert summary["high_risk"] is False

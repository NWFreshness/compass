# Compass Phase 4 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver Phase 4 in three independent sections — Reports (CSV + PDF downloads), Audit Log (write events + role-scoped UI), and Visual Polish (score color coding, subject performance bars, skeleton states) — with browser testing and a GitHub push after each section.

**Architecture:** Backend-first for reports and audit log (FastAPI → fpdf2/csv → StreamingResponse); audit events written inline in existing route handlers via a shared `log_action` helper; visual polish is purely frontend Tailwind/React work with no new API surface.

**Tech Stack:** Python `fpdf2` for PDF generation; Python `csv` stdlib for CSV; Alembic batch migrations for SQLite schema changes; Next.js App Router with Tailwind for frontend.

---

## SECTION 1 — REPORTS

---

### Task 1: Report schemas and data-assembly service

**Files:**
- Create: `backend/app/schemas/reports.py`
- Create: `backend/app/services/reports.py`
- Create: `backend/app/tests/test_reports.py` (partial — seed helpers + first tests)

---

- [ ] **Step 1: Add fpdf2 dependency**

```bash
cd backend && uv add fpdf2
```

Expected: `fpdf2` added to `pyproject.toml` dependencies.

---

- [ ] **Step 2: Write failing tests for report data assembly**

Create `backend/app/tests/test_reports.py`:

```python
from datetime import date
import pytest
from app.models import (
    Base, Class, School, Score, ScoreType, Student, Subject, User, UserRole,
    Intervention, InterventionStatus,
)
from app.schemas.reports import (
    StudentReportData, ClassReportData, SchoolReportData, DistrictReportData,
)
from app.services.reports import (
    build_student_report_data, build_class_report_data,
    build_school_report_data, build_district_report_data,
)
from app.services.auth import hash_password
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


def make_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)(), engine


def seed_report_world(db):
    school = School(name="Test School")
    db.add(school)
    db.flush()
    math = Subject(name="Math")
    reading = Subject(name="Reading")
    db.add_all([math, reading])
    db.flush()
    teacher = User(
        username="report_teacher",
        hashed_password=hash_password("pw"),
        role=UserRole.teacher,
        school_id=school.id,
    )
    db.add(teacher)
    db.flush()
    cls = Class(name="3A", grade_level=3, school_id=school.id, teacher_id=teacher.id)
    db.add(cls)
    db.flush()
    student = Student(
        name="Alice",
        student_id_number="A001",
        grade_level=3,
        school_id=school.id,
        class_id=cls.id,
    )
    db.add(student)
    db.flush()
    db.add_all([
        Score(student_id=student.id, subject_id=math.id, score_type=ScoreType.quiz, value=85.0, date=date(2026, 3, 1)),
        Score(student_id=student.id, subject_id=math.id, score_type=ScoreType.test, value=75.0, date=date(2026, 3, 15)),
        Score(student_id=student.id, subject_id=reading.id, score_type=ScoreType.quiz, value=60.0, date=date(2026, 3, 5)),
    ])
    db.commit()
    return {
        "school": school, "math": math, "reading": reading,
        "teacher": teacher, "cls": cls, "student": student,
    }


def test_build_student_report_data_returns_subject_averages():
    db, engine = make_db()
    try:
        world = seed_report_world(db)
        data = build_student_report_data(db, world["student"])
        assert isinstance(data, StudentReportData)
        assert data.student_name == "Alice"
        assert data.grade_level == 3
        subject_names = {s.subject_name for s in data.subject_averages}
        assert "Math" in subject_names
        assert "Reading" in subject_names
        math_avg = next(s for s in data.subject_averages if s.subject_name == "Math")
        assert math_avg.average == pytest.approx(80.0)
        assert math_avg.tier == "tier1"
        reading_avg = next(s for s in data.subject_averages if s.subject_name == "Reading")
        assert reading_avg.tier == "tier3"
    finally:
        db.close()
        engine.dispose()


def test_build_class_report_data_includes_all_students():
    db, engine = make_db()
    try:
        world = seed_report_world(db)
        data = build_class_report_data(db, world["cls"])
        assert isinstance(data, ClassReportData)
        assert data.class_name == "3A"
        assert data.student_count == 1
        assert len(data.students) == 1
        assert data.students[0].student_name == "Alice"
    finally:
        db.close()
        engine.dispose()


def test_build_school_report_data():
    db, engine = make_db()
    try:
        world = seed_report_world(db)
        data = build_school_report_data(db, world["school"])
        assert isinstance(data, SchoolReportData)
        assert data.school_name == "Test School"
        assert data.total_students == 1
        assert len(data.classes) == 1
    finally:
        db.close()
        engine.dispose()


def test_build_district_report_data():
    db, engine = make_db()
    try:
        world = seed_report_world(db)
        data = build_district_report_data(db)
        assert isinstance(data, DistrictReportData)
        assert data.total_students >= 1
        assert len(data.schools) >= 1
    finally:
        db.close()
        engine.dispose()
```

---

- [ ] **Step 3: Run tests to verify they fail**

```bash
cd backend && uv run pytest app/tests/test_reports.py -v
```

Expected: ImportError or AttributeError (modules don't exist yet).

---

- [ ] **Step 4: Create `app/schemas/reports.py`**

```python
from typing import Optional
from pydantic import BaseModel


class SubjectAverage(BaseModel):
    subject_name: str
    average: float
    tier: str


class StudentReportData(BaseModel):
    student_name: str
    student_id_number: str
    grade_level: int
    class_name: Optional[str]
    school_name: str
    subject_averages: list[SubjectAverage]
    intervention_count: int
    latest_ai_recommendation: Optional[str]


class ClassStudentRow(BaseModel):
    student_name: str
    avg_score: Optional[float]
    tier: Optional[str]


class ClassReportData(BaseModel):
    class_name: str
    grade_level: int
    school_name: str
    students: list[ClassStudentRow]
    tier_distribution: dict[str, int]
    student_count: int


class ClassSummaryRow(BaseModel):
    class_name: str
    grade_level: int
    student_count: int
    avg_score: Optional[float]
    tier_distribution: dict[str, int]


class SchoolReportData(BaseModel):
    school_name: str
    total_students: int
    classes: list[ClassSummaryRow]
    grade_averages: list[dict]
    at_risk_count: int


class SchoolSummaryRow(BaseModel):
    school_name: str
    student_count: int
    avg_score: Optional[float]
    tier_distribution: dict[str, int]
    high_risk: bool


class DistrictReportData(BaseModel):
    total_students: int
    tier_distribution: dict[str, int]
    schools: list[SchoolSummaryRow]
```

---

- [ ] **Step 5: Create `app/services/reports.py`**

```python
import csv
import io
from collections import defaultdict
from typing import Optional

from fpdf import FPDF
from sqlalchemy.orm import Session

from app.models import AIRec, AITargetType, Class, Intervention, School, Score, Student, Subject
from app.schemas.reports import (
    ClassReportData, ClassStudentRow, ClassSummaryRow,
    DistrictReportData, SchoolReportData, SchoolSummaryRow,
    StudentReportData, SubjectAverage,
)
from app.services.mtss import calculate_tier


# ---------------------------------------------------------------------------
# Data assembly
# ---------------------------------------------------------------------------

def build_student_report_data(db: Session, student: Student) -> StudentReportData:
    scores = db.query(Score).filter(Score.student_id == student.id).all()
    subject_ids = {s.subject_id for s in scores}
    subjects = {sub.id: sub.name for sub in db.query(Subject).filter(Subject.id.in_(subject_ids)).all()}

    by_subject: dict = defaultdict(list)
    for score in scores:
        by_subject[score.subject_id].append(score.value)

    subject_averages = []
    for subject_id, values in by_subject.items():
        avg = sum(values) / len(values)
        tier = calculate_tier(avg)
        subject_averages.append(SubjectAverage(
            subject_name=subjects.get(subject_id, str(subject_id)),
            average=round(avg, 1),
            tier=tier.value,
        ))
    subject_averages.sort(key=lambda s: s.subject_name)

    intervention_count = db.query(Intervention).filter(Intervention.student_id == student.id).count()

    latest_ai = (
        db.query(AIRec)
        .filter(AIRec.student_id == student.id, AIRec.target_type == AITargetType.student)
        .order_by(AIRec.created_at.desc())
        .first()
    )

    class_name: Optional[str] = None
    if student.class_id:
        cls = db.query(Class).filter(Class.id == student.class_id).first()
        class_name = cls.name if cls else None

    school = db.query(School).filter(School.id == student.school_id).first()
    school_name = school.name if school else str(student.school_id)

    return StudentReportData(
        student_name=student.name,
        student_id_number=student.student_id_number,
        grade_level=student.grade_level,
        class_name=class_name,
        school_name=school_name,
        subject_averages=subject_averages,
        intervention_count=intervention_count,
        latest_ai_recommendation=latest_ai.response[:500] if latest_ai else None,
    )


def build_class_report_data(db: Session, cls: Class) -> ClassReportData:
    students = db.query(Student).filter(Student.class_id == cls.id).all()
    student_ids = [s.id for s in students]

    scores_map: dict = defaultdict(list)
    for row in db.query(Score).filter(Score.student_id.in_(student_ids)).all():
        scores_map[row.student_id].append(row.value)

    tier_counts = {"tier1": 0, "tier2": 0, "tier3": 0}
    rows = []
    for student in sorted(students, key=lambda s: s.name):
        vals = scores_map.get(student.id, [])
        if vals:
            avg = round(sum(vals) / len(vals), 1)
            tier = calculate_tier(avg).value
            tier_counts[tier] += 1
        else:
            avg = None
            tier = None
        rows.append(ClassStudentRow(student_name=student.name, avg_score=avg, tier=tier))

    school = db.query(School).filter(School.id == cls.school_id).first()
    school_name = school.name if school else str(cls.school_id)

    return ClassReportData(
        class_name=cls.name,
        grade_level=cls.grade_level,
        school_name=school_name,
        students=rows,
        tier_distribution=tier_counts,
        student_count=len(students),
    )


def build_school_report_data(db: Session, school: School) -> SchoolReportData:
    classes = db.query(Class).filter(Class.school_id == school.id).all()
    class_ids = [c.id for c in classes]
    students = db.query(Student).filter(Student.class_id.in_(class_ids)).all()

    scores_map: dict = defaultdict(list)
    for row in db.query(Score).filter(Score.student_id.in_([s.id for s in students])).all():
        scores_map[row.student_id].append(row.value)

    class_summaries = []
    for cls in sorted(classes, key=lambda c: (c.grade_level, c.name)):
        cls_students = [s for s in students if s.class_id == cls.id]
        tier_counts = {"tier1": 0, "tier2": 0, "tier3": 0}
        avgs = []
        for s in cls_students:
            vals = scores_map.get(s.id, [])
            if vals:
                avg = sum(vals) / len(vals)
                avgs.append(avg)
                tier_counts[calculate_tier(avg).value] += 1
        class_summaries.append(ClassSummaryRow(
            class_name=cls.name,
            grade_level=cls.grade_level,
            student_count=len(cls_students),
            avg_score=round(sum(avgs) / len(avgs), 1) if avgs else None,
            tier_distribution=tier_counts,
        ))

    grade_avgs: dict = defaultdict(list)
    for s in students:
        vals = scores_map.get(s.id, [])
        if vals:
            grade_avgs[s.grade_level].append(sum(vals) / len(vals))

    grade_averages = [
        {"grade_level": g, "avg_score": round(sum(v) / len(v), 1), "student_count": len(v)}
        for g, v in sorted(grade_avgs.items())
    ]

    at_risk_count = sum(
        1 for s in students
        if scores_map.get(s.id) and calculate_tier(sum(scores_map[s.id]) / len(scores_map[s.id])).value in ("tier2", "tier3")
    )

    return SchoolReportData(
        school_name=school.name,
        total_students=len(students),
        classes=class_summaries,
        grade_averages=grade_averages,
        at_risk_count=at_risk_count,
    )


def build_district_report_data(db: Session) -> DistrictReportData:
    schools = db.query(School).all()
    total_students = 0
    all_tier_counts = {"tier1": 0, "tier2": 0, "tier3": 0}
    school_rows = []

    for school in schools:
        summary = _school_summary_fast(db, school)
        total_students += summary["student_count"]
        for k in all_tier_counts:
            all_tier_counts[k] += summary["tier_distribution"][k]
        school_rows.append(SchoolSummaryRow(
            school_name=school.name,
            student_count=summary["student_count"],
            avg_score=summary["avg_score"],
            tier_distribution=summary["tier_distribution"],
            high_risk=summary["high_risk"],
        ))

    return DistrictReportData(
        total_students=total_students,
        tier_distribution=all_tier_counts,
        schools=school_rows,
    )


def _school_summary_fast(db: Session, school: School) -> dict:
    class_ids = [c.id for c in db.query(Class).filter(Class.school_id == school.id).all()]
    students = db.query(Student).filter(Student.class_id.in_(class_ids)).all() if class_ids else []
    if not students:
        return {"student_count": 0, "avg_score": None, "tier_distribution": {"tier1": 0, "tier2": 0, "tier3": 0}, "high_risk": False}
    scores_map: dict = defaultdict(list)
    for row in db.query(Score).filter(Score.student_id.in_([s.id for s in students])).all():
        scores_map[row.student_id].append(row.value)
    tier_counts = {"tier1": 0, "tier2": 0, "tier3": 0}
    avgs = []
    for s in students:
        vals = scores_map.get(s.id, [])
        if vals:
            avg = sum(vals) / len(vals)
            avgs.append(avg)
            tier_counts[calculate_tier(avg).value] += 1
    total = len(students)
    return {
        "student_count": total,
        "avg_score": round(sum(avgs) / len(avgs), 1) if avgs else None,
        "tier_distribution": tier_counts,
        "high_risk": (tier_counts["tier3"] / total > 0.30) if total > 0 else False,
    }


# ---------------------------------------------------------------------------
# CSV renderers
# ---------------------------------------------------------------------------

def to_csv_student(data: StudentReportData) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Student Report"])
    w.writerow(["Name", data.student_name])
    w.writerow(["Student ID", data.student_id_number])
    w.writerow(["Grade", data.grade_level])
    w.writerow(["Class", data.class_name or "Unassigned"])
    w.writerow(["School", data.school_name])
    w.writerow(["Active Interventions", data.intervention_count])
    w.writerow([])
    w.writerow(["Subject", "Average Score", "Tier"])
    for s in data.subject_averages:
        w.writerow([s.subject_name, f"{s.average:.1f}", s.tier])
    if data.latest_ai_recommendation:
        w.writerow([])
        w.writerow(["Latest AI Recommendation"])
        w.writerow([data.latest_ai_recommendation])
    return buf.getvalue()


def to_csv_class(data: ClassReportData) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Class Report"])
    w.writerow(["Class", data.class_name])
    w.writerow(["Grade", data.grade_level])
    w.writerow(["School", data.school_name])
    w.writerow(["Total Students", data.student_count])
    w.writerow(["Tier 1", data.tier_distribution["tier1"]])
    w.writerow(["Tier 2", data.tier_distribution["tier2"]])
    w.writerow(["Tier 3", data.tier_distribution["tier3"]])
    w.writerow([])
    w.writerow(["Student", "Avg Score", "Tier"])
    for row in data.students:
        w.writerow([row.student_name, f"{row.avg_score:.1f}" if row.avg_score is not None else "—", row.tier or "—"])
    return buf.getvalue()


def to_csv_school(data: SchoolReportData) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["School Report"])
    w.writerow(["School", data.school_name])
    w.writerow(["Total Students", data.total_students])
    w.writerow(["At-Risk Students", data.at_risk_count])
    w.writerow([])
    w.writerow(["Class", "Grade", "Students", "Avg Score", "Tier 1", "Tier 2", "Tier 3"])
    for cls in data.classes:
        w.writerow([
            cls.class_name, cls.grade_level, cls.student_count,
            f"{cls.avg_score:.1f}" if cls.avg_score is not None else "—",
            cls.tier_distribution["tier1"], cls.tier_distribution["tier2"], cls.tier_distribution["tier3"],
        ])
    if data.grade_averages:
        w.writerow([])
        w.writerow(["Grade Averages"])
        w.writerow(["Grade", "Avg Score", "Students"])
        for g in data.grade_averages:
            w.writerow([g["grade_level"], g["avg_score"], g["student_count"]])
    return buf.getvalue()


def to_csv_district(data: DistrictReportData) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["District Report"])
    w.writerow(["Total Students", data.total_students])
    w.writerow(["Tier 1", data.tier_distribution["tier1"]])
    w.writerow(["Tier 2", data.tier_distribution["tier2"]])
    w.writerow(["Tier 3", data.tier_distribution["tier3"]])
    w.writerow([])
    w.writerow(["School", "Students", "Avg Score", "Tier 1", "Tier 2", "Tier 3", "High Risk"])
    for school in data.schools:
        w.writerow([
            school.school_name, school.student_count,
            f"{school.avg_score:.1f}" if school.avg_score is not None else "—",
            school.tier_distribution["tier1"], school.tier_distribution["tier2"], school.tier_distribution["tier3"],
            "Yes" if school.high_risk else "No",
        ])
    return buf.getvalue()


# ---------------------------------------------------------------------------
# PDF renderers
# ---------------------------------------------------------------------------

def _base_pdf(title: str) -> FPDF:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 12, title, new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Helvetica", "", 10)
    return pdf


def _pdf_row(pdf: FPDF, label: str, value: str) -> None:
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(55, 7, label + ":", new_x="RIGHT", new_y="TOP")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 7, value, new_x="LMARGIN", new_y="NEXT")


def _pdf_table_header(pdf: FPDF, cols: list[tuple[str, int]]) -> None:
    pdf.set_fill_color(241, 245, 249)
    pdf.set_font("Helvetica", "B", 9)
    for label, width in cols:
        pdf.cell(width, 7, label, border=1, fill=True)
    pdf.ln()


def _pdf_table_row(pdf: FPDF, values: list[tuple[str, int]]) -> None:
    pdf.set_font("Helvetica", "", 9)
    for value, width in values:
        pdf.cell(width, 6, value, border=1)
    pdf.ln()


def to_pdf_student(data: StudentReportData) -> bytes:
    pdf = _base_pdf(f"Student Report — {data.student_name}")
    _pdf_row(pdf, "Student ID", data.student_id_number)
    _pdf_row(pdf, "Grade", str(data.grade_level))
    _pdf_row(pdf, "Class", data.class_name or "Unassigned")
    _pdf_row(pdf, "School", data.school_name)
    _pdf_row(pdf, "Active Interventions", str(data.intervention_count))
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "Subject Performance", new_x="LMARGIN", new_y="NEXT")
    _pdf_table_header(pdf, [("Subject", 70), ("Avg Score", 40), ("Tier", 40)])
    for s in data.subject_averages:
        _pdf_table_row(pdf, [(s.subject_name, 70), (f"{s.average:.1f}", 40), (s.tier.replace("tier", "Tier "), 40)])
    if data.latest_ai_recommendation:
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, "Latest AI Recommendation", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(0, 5, data.latest_ai_recommendation)
    return bytes(pdf.output())


def to_pdf_class(data: ClassReportData) -> bytes:
    pdf = _base_pdf(f"Class Report — {data.class_name}")
    _pdf_row(pdf, "Grade", str(data.grade_level))
    _pdf_row(pdf, "School", data.school_name)
    _pdf_row(pdf, "Students", str(data.student_count))
    _pdf_row(pdf, "Tier 1 / 2 / 3", f"{data.tier_distribution['tier1']} / {data.tier_distribution['tier2']} / {data.tier_distribution['tier3']}")
    pdf.ln(4)
    _pdf_table_header(pdf, [("Student", 90), ("Avg Score", 45), ("Tier", 45)])
    for row in data.students:
        _pdf_table_row(pdf, [
            (row.student_name, 90),
            (f"{row.avg_score:.1f}" if row.avg_score is not None else "—", 45),
            ((row.tier or "—").replace("tier", "Tier "), 45),
        ])
    return bytes(pdf.output())


def to_pdf_school(data: SchoolReportData) -> bytes:
    pdf = _base_pdf(f"School Report — {data.school_name}")
    _pdf_row(pdf, "Total Students", str(data.total_students))
    _pdf_row(pdf, "At-Risk Students", str(data.at_risk_count))
    pdf.ln(4)
    _pdf_table_header(pdf, [("Class", 55), ("Gr", 12), ("Students", 25), ("Avg", 20), ("T1", 18), ("T2", 18), ("T3", 18)])
    for cls in data.classes:
        _pdf_table_row(pdf, [
            (cls.class_name, 55), (str(cls.grade_level), 12), (str(cls.student_count), 25),
            (f"{cls.avg_score:.1f}" if cls.avg_score is not None else "—", 20),
            (str(cls.tier_distribution["tier1"]), 18),
            (str(cls.tier_distribution["tier2"]), 18),
            (str(cls.tier_distribution["tier3"]), 18),
        ])
    if data.grade_averages:
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, "Grade Averages", new_x="LMARGIN", new_y="NEXT")
        _pdf_table_header(pdf, [("Grade", 40), ("Avg Score", 50), ("Students", 50)])
        for g in data.grade_averages:
            _pdf_table_row(pdf, [(str(g["grade_level"]), 40), (str(g["avg_score"]), 50), (str(g["student_count"]), 50)])
    return bytes(pdf.output())


def to_pdf_district(data: DistrictReportData) -> bytes:
    pdf = _base_pdf("District Report")
    _pdf_row(pdf, "Total Students", str(data.total_students))
    _pdf_row(pdf, "Tier 1 / 2 / 3", f"{data.tier_distribution['tier1']} / {data.tier_distribution['tier2']} / {data.tier_distribution['tier3']}")
    pdf.ln(4)
    _pdf_table_header(pdf, [("School", 65), ("Students", 25), ("Avg", 20), ("T1", 18), ("T2", 18), ("T3", 18), ("Risk", 18)])
    for school in data.schools:
        _pdf_table_row(pdf, [
            (school.school_name, 65), (str(school.student_count), 25),
            (f"{school.avg_score:.1f}" if school.avg_score is not None else "—", 20),
            (str(school.tier_distribution["tier1"]), 18),
            (str(school.tier_distribution["tier2"]), 18),
            (str(school.tier_distribution["tier3"]), 18),
            ("High" if school.high_risk else "OK", 18),
        ])
    return bytes(pdf.output())
```

---

- [ ] **Step 6: Run tests to verify they pass**

```bash
cd backend && uv run pytest app/tests/test_reports.py -v
```

Expected: all 4 tests PASS.

---

- [ ] **Step 7: Commit**

```bash
cd backend && git add app/schemas/reports.py app/services/reports.py app/tests/test_reports.py pyproject.toml uv.lock && git commit -m "feat: add report schemas, data assembly service, and tests"
```

---

### Task 2: Report routes

**Files:**
- Create: `backend/app/routes/reports.py`
- Modify: `backend/app/main.py`

---

- [ ] **Step 1: Add route tests to `app/tests/test_reports.py`**

Append these tests to the existing file:

```python
from app.services.auth import hash_password as _hp


def seed_for_routes(db):
    school = School(name="Route School")
    db.add(school)
    db.flush()
    subj = Subject(name="Science")
    db.add(subj)
    db.flush()
    teacher = User(username="r_teacher", hashed_password=_hp("pw"), role=UserRole.teacher, school_id=school.id)
    principal = User(username="r_principal", hashed_password=_hp("pw"), role=UserRole.principal, school_id=school.id)
    it_admin = User(username="r_admin", hashed_password=_hp("pw"), role=UserRole.it_admin)
    db.add_all([teacher, principal, it_admin])
    db.flush()
    cls = Class(name="5B", grade_level=5, school_id=school.id, teacher_id=teacher.id)
    db.add(cls)
    db.flush()
    student = Student(name="Bob", student_id_number="B002", grade_level=5, school_id=school.id, class_id=cls.id)
    db.add(student)
    db.flush()
    db.add(Score(student_id=student.id, subject_id=subj.id, score_type=ScoreType.quiz, value=88.0, date=date(2026, 4, 1)))
    db.commit()
    return {"school": school, "cls": cls, "student": student, "teacher": teacher, "it_admin": it_admin}


def login_as(client, username):
    r = client.post("/api/auth/login", json={"username": username, "password": "pw"})
    assert r.status_code == 200


def test_student_report_csv_returns_csv(client, db):
    world = seed_for_routes(db)
    login_as(client, "r_teacher")
    r = client.get(f"/api/reports/student/{world['student'].id}?format=csv")
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]


def test_student_report_pdf_returns_pdf(client, db):
    world = seed_for_routes(db)
    login_as(client, "r_teacher")
    r = client.get(f"/api/reports/student/{world['student'].id}?format=pdf")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"


def test_class_report_csv(client, db):
    world = seed_for_routes(db)
    login_as(client, "r_teacher")
    r = client.get(f"/api/reports/class/{world['cls'].id}?format=csv")
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]


def test_school_report_csv(client, db):
    world = seed_for_routes(db)
    login_as(client, "r_principal")
    r = client.get(f"/api/reports/school/{world['school'].id}?format=csv")
    assert r.status_code == 200


def test_district_report_requires_admin(client, db):
    seed_for_routes(db)
    login_as(client, "r_teacher")
    r = client.get("/api/reports/district?format=csv")
    assert r.status_code == 403


def test_district_report_csv_for_admin(client, db):
    seed_for_routes(db)
    login_as(client, "r_admin")
    r = client.get("/api/reports/district?format=csv")
    assert r.status_code == 200


def test_report_requires_auth(client, db):
    world = seed_for_routes(db)
    r = client.get(f"/api/reports/student/{world['student'].id}?format=csv")
    assert r.status_code == 401
```

---

- [ ] **Step 2: Run new tests to verify they fail**

```bash
cd backend && uv run pytest app/tests/test_reports.py::test_student_report_csv_returns_csv -v
```

Expected: FAIL — no route registered.

---

- [ ] **Step 3: Create `app/routes/reports.py`**

```python
import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db import get_db
from app.middleware.auth import get_current_user, require_role
from app.models import Class, School, Student, User, UserRole
from app.services.reports import (
    build_class_report_data, build_district_report_data,
    build_school_report_data, build_student_report_data,
    to_csv_class, to_csv_district, to_csv_school, to_csv_student,
    to_pdf_class, to_pdf_district, to_pdf_school, to_pdf_student,
)

router = APIRouter(prefix="/api/reports", tags=["reports"])

Format = Literal["csv", "pdf"]


def _csv_response(content: str, filename: str) -> Response:
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


def _pdf_response(content: bytes, filename: str) -> Response:
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


def _assert_student_access(db: Session, user: User, student: Student) -> None:
    if user.role in (UserRole.it_admin, UserRole.district_admin):
        return
    if user.role == UserRole.principal:
        if student.school_id != user.school_id:
            raise HTTPException(status_code=403, detail="Outside your school")
        return
    if user.role == UserRole.teacher:
        class_ids = [
            c.id for c in db.query(Class).filter(Class.teacher_id == user.id).all()
        ]
        if student.class_id not in class_ids:
            raise HTTPException(status_code=403, detail="Student is not in your class")
        return
    raise HTTPException(status_code=403, detail="Insufficient permissions")


def _assert_class_access(db: Session, user: User, cls: Class) -> None:
    if user.role in (UserRole.it_admin, UserRole.district_admin):
        return
    if user.role == UserRole.principal:
        if cls.school_id != user.school_id:
            raise HTTPException(status_code=403, detail="Outside your school")
        return
    if user.role == UserRole.teacher:
        if cls.teacher_id != user.id:
            raise HTTPException(status_code=403, detail="You do not teach this class")
        return
    raise HTTPException(status_code=403, detail="Insufficient permissions")


def _assert_school_access(user: User, school: School) -> None:
    if user.role in (UserRole.it_admin, UserRole.district_admin):
        return
    if user.role == UserRole.principal:
        if school.id != user.school_id:
            raise HTTPException(status_code=403, detail="Outside your school")
        return
    raise HTTPException(status_code=403, detail="Insufficient permissions")


@router.get("/student/{student_id}")
def student_report(
    student_id: uuid.UUID,
    format: Format = Query("csv"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    _assert_student_access(db, current_user, student)
    data = build_student_report_data(db, student)
    slug = student.student_id_number
    if format == "pdf":
        return _pdf_response(to_pdf_student(data), f"student_{slug}.pdf")
    return _csv_response(to_csv_student(data), f"student_{slug}.csv")


@router.get("/class/{class_id}")
def class_report(
    class_id: uuid.UUID,
    format: Format = Query("csv"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    cls = db.query(Class).filter(Class.id == class_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
    _assert_class_access(db, current_user, cls)
    data = build_class_report_data(db, cls)
    slug = cls.name.replace(" ", "_")
    if format == "pdf":
        return _pdf_response(to_pdf_class(data), f"class_{slug}.pdf")
    return _csv_response(to_csv_class(data), f"class_{slug}.csv")


@router.get("/school/{school_id}")
def school_report(
    school_id: uuid.UUID,
    format: Format = Query("csv"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    _assert_school_access(current_user, school)
    data = build_school_report_data(db, school)
    slug = school.name.replace(" ", "_")
    if format == "pdf":
        return _pdf_response(to_pdf_school(data), f"school_{slug}.pdf")
    return _csv_response(to_csv_school(data), f"school_{slug}.csv")


@router.get("/district")
def district_report(
    format: Format = Query("csv"),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.it_admin, UserRole.district_admin)
    ),
) -> Response:
    data = build_district_report_data(db)
    if format == "pdf":
        return _pdf_response(to_pdf_district(data), "district_report.pdf")
    return _csv_response(to_csv_district(data), "district_report.csv")
```

---

- [ ] **Step 4: Register router in `app/main.py`**

Add to imports:
```python
from app.routes.reports import router as reports_router
```

Add to router registrations:
```python
app.include_router(reports_router)
```

---

- [ ] **Step 5: Run all report tests**

```bash
cd backend && uv run pytest app/tests/test_reports.py -v
```

Expected: all tests PASS.

---

- [ ] **Step 6: Commit**

```bash
cd backend && git add app/routes/reports.py app/main.py && git commit -m "feat: add report routes (CSV + PDF) for student, class, school, district"
```

---

### Task 3: Frontend reports page and student profile export

**Files:**
- Create: `frontend/src/app/(protected)/reports/page.tsx`
- Modify: `frontend/src/components/layout/sidebar.tsx`
- Modify: `frontend/src/app/(protected)/students/[id]/page.tsx`

---

- [ ] **Step 1: Create `frontend/src/app/(protected)/reports/page.tsx`**

```tsx
"use client";

import { useEffect, useState } from "react";
import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import type { Class, School, Student } from "@/lib/types";

type ReportType = "student" | "class" | "school" | "district";
type ReportFormat = "csv" | "pdf";

async function triggerDownload(path: string, filename: string) {
  const res = await fetch(`/api${path}`, { credentials: "include" });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export default function ReportsPage() {
  const { user } = useAuth();
  const [reportType, setReportType] = useState<ReportType>("student");
  const [format, setFormat] = useState<ReportFormat>("csv");
  const [students, setStudents] = useState<Student[]>([]);
  const [classes, setClasses] = useState<Class[]>([]);
  const [schools, setSchools] = useState<School[]>([]);
  const [selectedStudent, setSelectedStudent] = useState("");
  const [selectedClass, setSelectedClass] = useState("");
  const [selectedSchool, setSelectedSchool] = useState("");
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const [s, c, sc] = await Promise.all([
          api.get<Student[]>("/students"),
          api.get<Class[]>("/lookups/classes"),
          api.get<School[]>("/lookups/schools"),
        ]);
        setStudents(s);
        setClasses(c);
        setSchools(sc);
        if (s[0]) setSelectedStudent(s[0].id);
        if (c[0]) setSelectedClass(c[0].id);
        if (sc[0]) setSelectedSchool(sc[0].id);
      } catch {}
    }
    void load();
  }, []);

  const canDistrict = user?.role === "it_admin" || user?.role === "district_admin";
  const canSchool = canDistrict || user?.role === "principal";

  const availableTypes: { value: ReportType; label: string }[] = [
    { value: "student", label: "Student Report" },
    { value: "class", label: "Class Report" },
    ...(canSchool ? [{ value: "school" as ReportType, label: "School Report" }] : []),
    ...(canDistrict ? [{ value: "district" as ReportType, label: "District Report" }] : []),
  ];

  async function handleDownload() {
    setError("");
    setDownloading(true);
    try {
      let path = "";
      let filename = "";
      if (reportType === "student" && selectedStudent) {
        path = `/reports/student/${selectedStudent}?format=${format}`;
        filename = `student_report.${format}`;
      } else if (reportType === "class" && selectedClass) {
        path = `/reports/class/${selectedClass}?format=${format}`;
        filename = `class_report.${format}`;
      } else if (reportType === "school" && selectedSchool) {
        path = `/reports/school/${selectedSchool}?format=${format}`;
        filename = `school_report.${format}`;
      } else if (reportType === "district") {
        path = `/reports/district?format=${format}`;
        filename = `district_report.${format}`;
      }
      if (!path) { setError("Please select a target."); return; }
      await triggerDownload(path, filename);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Download failed");
    } finally {
      setDownloading(false);
    }
  }

  return (
    <div>
      <Header title="Reports" />
      <div className="space-y-4 p-6 max-w-lg">
        <Card>
          <CardContent className="space-y-4 p-6">
            <div className="space-y-1">
              <label className="text-sm font-medium">Report Type</label>
              <Select value={reportType} onValueChange={(v) => setReportType(v as ReportType)}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {availableTypes.map((t) => (
                    <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {reportType === "student" && (
              <div className="space-y-1">
                <label className="text-sm font-medium">Student</label>
                <Select value={selectedStudent} onValueChange={setSelectedStudent}>
                  <SelectTrigger><SelectValue placeholder="Select student" /></SelectTrigger>
                  <SelectContent>
                    {students.map((s) => (
                      <SelectItem key={s.id} value={s.id}>{s.name} ({s.student_id_number})</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            {reportType === "class" && (
              <div className="space-y-1">
                <label className="text-sm font-medium">Class</label>
                <Select value={selectedClass} onValueChange={setSelectedClass}>
                  <SelectTrigger><SelectValue placeholder="Select class" /></SelectTrigger>
                  <SelectContent>
                    {classes.map((c) => (
                      <SelectItem key={c.id} value={c.id}>{c.name} (Grade {c.grade_level})</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            {reportType === "school" && (
              <div className="space-y-1">
                <label className="text-sm font-medium">School</label>
                <Select value={selectedSchool} onValueChange={setSelectedSchool}>
                  <SelectTrigger><SelectValue placeholder="Select school" /></SelectTrigger>
                  <SelectContent>
                    {schools.map((s) => (
                      <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            <div className="space-y-1">
              <label className="text-sm font-medium">Format</label>
              <Select value={format} onValueChange={(v) => setFormat(v as ReportFormat)}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="csv">CSV</SelectItem>
                  <SelectItem value="pdf">PDF</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {error && <p className="text-sm text-red-600">{error}</p>}

            <Button onClick={() => void handleDownload()} disabled={downloading} className="w-full">
              {downloading ? "Downloading..." : "Download Report"}
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
```

---

- [ ] **Step 2: Add "Reports" to sidebar in `frontend/src/components/layout/sidebar.tsx`**

Add the import at the top with the other lucide icons:
```tsx
import { ..., FileText } from "lucide-react";
```

Add to the `NAV` array (after the Import Scores entry):
```tsx
{ href: "/reports", label: "Reports", icon: FileText, roles: ["it_admin", "district_admin", "principal", "teacher"] },
```

---

- [ ] **Step 3: Add export button to student profile in `frontend/src/app/(protected)/students/[id]/page.tsx`**

Add a `triggerDownload` helper and an export dropdown. Add this function inside the component (before the return):

```tsx
async function handleExport(fmt: "csv" | "pdf") {
  try {
    const res = await fetch(`/api/reports/student/${params.id}?format=${fmt}`, {
      credentials: "include",
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `student_report.${fmt}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  } catch (err: unknown) {
    setError(err instanceof Error ? err.message : "Export failed");
  }
}
```

Replace the existing `<Link href="/students" ...>Back to Students</Link>` line with:

```tsx
<div className="flex items-center gap-2">
  <Link href="/students" className={buttonVariants({ variant: "outline" })}>
    Back to Students
  </Link>
  {student && (
    <div className="flex gap-1">
      <button
        type="button"
        className={buttonVariants({ variant: "outline", size: "sm" })}
        onClick={() => void handleExport("csv")}
      >
        Export CSV
      </button>
      <button
        type="button"
        className={buttonVariants({ variant: "outline", size: "sm" })}
        onClick={() => void handleExport("pdf")}
      >
        Export PDF
      </button>
    </div>
  )}
</div>
```

---

- [ ] **Step 4: Verify frontend builds without errors**

```bash
cd frontend && npm run build 2>&1 | tail -20
```

Expected: Build completes without TypeScript errors.

---

- [ ] **Step 5: Commit**

```bash
git add frontend/src/app/\(protected\)/reports/page.tsx frontend/src/components/layout/sidebar.tsx frontend/src/app/\(protected\)/students/\[id\]/page.tsx && git commit -m "feat: add reports page, sidebar nav, and student profile export buttons"
```

---

## SECTION 2 — AUDIT LOG

---

### Task 4: Alembic migration, audit model update, service, and schemas

**Files:**
- Modify: `backend/app/models/audit_log.py`
- Create: `backend/alembic/versions/<hash>_add_school_id_to_audit_log.py`
- Create: `backend/app/services/audit.py`
- Create: `backend/app/schemas/audit.py`

---

- [ ] **Step 1: Update `app/models/audit_log.py` to add `school_id`**

```python
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    detail: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    school_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
```

---

- [ ] **Step 2: Generate Alembic migration**

```bash
cd backend && uv run alembic revision --autogenerate -m "add school_id to audit_log"
```

Expected: new file created in `alembic/versions/`.

Open the generated file and verify the `upgrade()` function contains:
```python
op.add_column('audit_log', sa.Column('school_id', sa.Uuid(), nullable=True))
```

If it doesn't, add it manually to `upgrade()`:
```python
def upgrade() -> None:
    op.add_column('audit_log', sa.Column('school_id', sa.Uuid(), nullable=True))

def downgrade() -> None:
    op.drop_column('audit_log', 'school_id')
```

---

- [ ] **Step 3: Apply migration**

```bash
cd backend && uv run alembic upgrade head
```

Expected: `Running upgrade ... -> <revision>  add school_id to audit_log`

---

- [ ] **Step 4: Create `app/schemas/audit.py`**

```python
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class AuditLogEntry(BaseModel):
    id: uuid.UUID
    user_id: Optional[uuid.UUID]
    action: str
    entity_type: str
    entity_id: Optional[str]
    detail: Optional[str]
    school_id: Optional[uuid.UUID]
    timestamp: datetime
    model_config = {"from_attributes": True}


class AuditLogPage(BaseModel):
    total: int
    entries: list[AuditLogEntry]
```

---

- [ ] **Step 5: Create `app/services/audit.py`**

```python
import uuid
from typing import Optional
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog


def log_action(
    db: Session,
    *,
    user_id: Optional[uuid.UUID],
    action: str,
    entity_type: str,
    entity_id: Optional[str] = None,
    detail: Optional[str] = None,
    school_id: Optional[uuid.UUID] = None,
) -> None:
    """Append an audit entry to the session. The caller's db.commit() persists it."""
    entry = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        detail=detail,
        school_id=school_id,
    )
    db.add(entry)
```

---

- [ ] **Step 6: Commit**

```bash
cd backend && git add app/models/audit_log.py app/schemas/audit.py app/services/audit.py alembic/versions/ && git commit -m "feat: add school_id to audit_log, audit schema, and log_action service"
```

---

### Task 5: Audit routes and wiring log_action into existing routes

**Files:**
- Create: `backend/app/routes/audit.py`
- Modify: `backend/app/main.py`
- Modify: `backend/app/routes/auth.py`
- Modify: `backend/app/routes/students.py`
- Modify: `backend/app/routes/scores.py`
- Modify: `backend/app/routes/interventions.py`
- Modify: `backend/app/routes/admin.py`
- Create: `backend/app/tests/test_audit.py`

---

- [ ] **Step 1: Write failing audit route tests**

Create `backend/app/tests/test_audit.py`:

```python
import pytest
from app.models import AuditLog, School, User, UserRole
from app.services.audit import log_action
from app.services.auth import hash_password
import uuid


def seed_audit_world(db):
    school1 = School(name="Audit School 1")
    school2 = School(name="Audit School 2")
    db.add_all([school1, school2])
    db.flush()
    it_admin = User(username="audit_it", hashed_password=hash_password("pw"), role=UserRole.it_admin)
    district_admin = User(
        username="audit_district",
        hashed_password=hash_password("pw"),
        role=UserRole.district_admin,
        school_id=school1.id,
    )
    teacher = User(username="audit_teacher", hashed_password=hash_password("pw"), role=UserRole.teacher, school_id=school1.id)
    db.add_all([it_admin, district_admin, teacher])
    db.commit()
    # Add entries for both schools
    log_action(db, user_id=it_admin.id, action="login", entity_type="user", entity_id=str(it_admin.id), school_id=None)
    log_action(db, user_id=district_admin.id, action="student.create", entity_type="student", entity_id=str(uuid.uuid4()), school_id=school1.id)
    log_action(db, user_id=teacher.id, action="score.create", entity_type="score", entity_id=str(uuid.uuid4()), school_id=school2.id)
    db.commit()
    return {"it_admin": it_admin, "district_admin": district_admin, "teacher": teacher, "school1": school1, "school2": school2}


def login_as(client, username):
    r = client.post("/api/auth/login", json={"username": username, "password": "pw"})
    assert r.status_code == 200


def test_it_admin_sees_all_audit_entries(client, db):
    world = seed_audit_world(db)
    login_as(client, "audit_it")
    r = client.get("/api/audit")
    assert r.status_code == 200
    data = r.json()
    # it_admin sees entries from both schools + null school entries
    assert data["total"] >= 3


def test_district_admin_sees_only_own_school_entries(client, db):
    world = seed_audit_world(db)
    login_as(client, "audit_district")
    r = client.get("/api/audit")
    assert r.status_code == 200
    data = r.json()
    # district_admin (school1) should see school1 entries only
    for entry in data["entries"]:
        assert entry["school_id"] == str(world["school1"].id)


def test_teacher_cannot_access_audit_log(client, db):
    seed_audit_world(db)
    login_as(client, "audit_teacher")
    r = client.get("/api/audit")
    assert r.status_code == 403


def test_audit_log_requires_auth(client, db):
    seed_audit_world(db)
    r = client.get("/api/audit")
    assert r.status_code == 401


def test_audit_log_pagination(client, db):
    world = seed_audit_world(db)
    login_as(client, "audit_it")
    r = client.get("/api/audit?page=1&per_page=2")
    assert r.status_code == 200
    data = r.json()
    assert len(data["entries"]) <= 2


def test_audit_log_action_filter(client, db):
    world = seed_audit_world(db)
    login_as(client, "audit_it")
    r = client.get("/api/audit?action=login")
    assert r.status_code == 200
    data = r.json()
    for entry in data["entries"]:
        assert entry["action"] == "login"
```

---

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && uv run pytest app/tests/test_audit.py -v
```

Expected: FAIL — no `/api/audit` route.

---

- [ ] **Step 3: Create `app/routes/audit.py`**

```python
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.middleware.auth import require_role
from app.models import AuditLog, User, UserRole
from app.schemas.audit import AuditLogPage

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("", response_model=AuditLogPage)
def list_audit_log(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.it_admin, UserRole.district_admin)),
) -> AuditLogPage:
    q = db.query(AuditLog)

    if current_user.role == UserRole.district_admin:
        q = q.filter(AuditLog.school_id == current_user.school_id)

    if action:
        q = q.filter(AuditLog.action == action)
    if entity_type:
        q = q.filter(AuditLog.entity_type == entity_type)
    if date_from:
        q = q.filter(AuditLog.timestamp >= date_from)
    if date_to:
        q = q.filter(AuditLog.timestamp <= date_to)

    total = q.count()
    entries = q.order_by(AuditLog.timestamp.desc()).offset((page - 1) * per_page).limit(per_page).all()
    return AuditLogPage(total=total, entries=entries)
```

---

- [ ] **Step 4: Register audit router in `app/main.py`**

Add import:
```python
from app.routes.audit import router as audit_router
```

Add registration:
```python
app.include_router(audit_router)
```

---

- [ ] **Step 5: Run audit tests to verify they pass**

```bash
cd backend && uv run pytest app/tests/test_audit.py -v
```

Expected: all 6 tests PASS.

---

- [ ] **Step 6: Wire `log_action` into `app/routes/auth.py`**

Add imports at the top:
```python
from app.services.audit import log_action
```

In `login` route, after `response.set_cookie(...)`:
```python
    log_action(db, user_id=user.id, action="login", entity_type="user", entity_id=str(user.id), school_id=user.school_id)
    db.commit()
```

In `logout` route, after `delete_session(db, session_id)`:
```python
        log_action(db, user_id=None, action="logout", entity_type="session", entity_id=session_id)
        db.commit()
```

---

- [ ] **Step 7: Wire `log_action` into `app/routes/students.py`**

Add import:
```python
from app.services.audit import log_action
```

In `create_student`, after `db.refresh(student)`:
```python
    log_action(db, user_id=current_user.id, action="student.create", entity_type="student", entity_id=str(student.id), school_id=student.school_id)
    db.commit()
```

In `update_student`, after `db.refresh(student)`:
```python
    log_action(db, user_id=current_user.id, action="student.update", entity_type="student", entity_id=str(student.id), school_id=student.school_id)
    db.commit()
```

---

- [ ] **Step 8: Wire `log_action` into `app/routes/scores.py`**

Add import:
```python
from app.services.audit import log_action
```

In `create_score`, after `db.refresh(score)`:
```python
    log_action(db, user_id=_.id if hasattr(_, 'id') else None, action="score.create", entity_type="score", entity_id=str(score.id))
    db.commit()
```

Wait — scores.py uses `_: User = Depends(get_current_user)`. Change the parameter name in `create_score` and `import_scores` to `current_user`:

Full updated `app/routes/scores.py`:
```python
import uuid
from fastapi import APIRouter, Depends, UploadFile
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from app.db import get_db
from app.middleware.auth import get_current_user
from app.models import Score, User
from app.schemas.score import ScoreCreate, ScoreResponse, CSVImportResult
from app.services.audit import log_action
from app.services.csv_import import parse_and_validate_csv

router = APIRouter(prefix="/api/scores", tags=["scores"])

CSV_TEMPLATE = "student_id_number,subject_name,score_type,value,date,notes\nS001,Math,quiz,85,2026-03-01,\n"


@router.get("/template.csv", response_class=PlainTextResponse)
def get_template(_: User = Depends(get_current_user)):
    return PlainTextResponse(
        content=CSV_TEMPLATE,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=scores_template.csv"},
    )


@router.post("", response_model=ScoreResponse, status_code=201)
def create_score(
    body: ScoreCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    score = Score(**body.model_dump())
    db.add(score)
    db.commit()
    db.refresh(score)
    log_action(db, user_id=current_user.id, action="score.create", entity_type="score", entity_id=str(score.id), school_id=current_user.school_id)
    db.commit()
    return score


@router.post("/import", response_model=CSVImportResult)
async def import_scores(
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contents = await file.read()
    result = parse_and_validate_csv(db, contents)
    log_action(db, user_id=current_user.id, action="score.import", entity_type="score", detail=f"{result.imported} rows imported", school_id=current_user.school_id)
    db.commit()
    return result


@router.get("/student/{student_id}", response_model=list[ScoreResponse])
def get_student_scores(
    student_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return db.query(Score).filter(Score.student_id == student_id).order_by(Score.date.desc()).all()
```

---

- [ ] **Step 9: Wire `log_action` into `app/routes/interventions.py`**

Add import:
```python
from app.services.audit import log_action
```

In `create_intervention`, after `db.refresh(intervention)`:
```python
    log_action(db, user_id=current_user.id, action="intervention.create", entity_type="intervention", entity_id=str(intervention.id), school_id=current_user.school_id)
    db.commit()
```

In `update_intervention`, after `db.refresh(intervention)`:
```python
    log_action(db, user_id=current_user.id, action="intervention.update", entity_type="intervention", entity_id=str(intervention.id), school_id=current_user.school_id)
    db.commit()
```

---

- [ ] **Step 10: Check `app/routes/admin.py` for user create/delete**

Read the file and add `log_action` calls after user creation and deletion. The pattern will match:

For user create (after `db.refresh(user)`):
```python
    log_action(db, user_id=current_user.id, action="user.create", entity_type="user", entity_id=str(user.id))
    db.commit()
```

For user delete (after `db.delete(user)` / `db.commit()`):
```python
    log_action(db, user_id=current_user.id, action="user.delete", entity_type="user", entity_id=str(user_id))
    db.commit()
```

---

- [ ] **Step 11: Run full test suite to verify no regressions**

```bash
cd backend && uv run pytest -v
```

Expected: all tests PASS (including pre-existing ones).

---

- [ ] **Step 12: Commit**

```bash
cd backend && git add app/routes/audit.py app/main.py app/routes/auth.py app/routes/students.py app/routes/scores.py app/routes/interventions.py app/routes/admin.py app/tests/test_audit.py && git commit -m "feat: add audit log route and wire log_action into all mutating routes"
```

---

### Task 6: Frontend audit log page

**Files:**
- Create: `frontend/src/app/(protected)/admin/audit/page.tsx`
- Modify: `frontend/src/components/layout/sidebar.tsx`
- Modify: `frontend/src/lib/types.ts`

---

- [ ] **Step 1: Add `AuditLogEntry` and `AuditLogPage` to `frontend/src/lib/types.ts`**

Append to the file:
```typescript
export interface AuditLogEntry {
  id: string;
  user_id: string | null;
  action: string;
  entity_type: string;
  entity_id: string | null;
  detail: string | null;
  school_id: string | null;
  timestamp: string;
}

export interface AuditLogPage {
  total: number;
  entries: AuditLogEntry[];
}
```

---

- [ ] **Step 2: Create `frontend/src/app/(protected)/admin/audit/page.tsx`**

```tsx
"use client";

import { useEffect, useState } from "react";
import { Header } from "@/components/layout/header";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { api } from "@/lib/api";
import type { AuditLogPage } from "@/lib/types";

const PER_PAGE = 50;

export default function AuditLogPage() {
  const [data, setData] = useState<AuditLogPage | null>(null);
  const [page, setPage] = useState(1);
  const [action, setAction] = useState("");
  const [entityType, setEntityType] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError("");
      try {
        const params = new URLSearchParams({ page: String(page), per_page: String(PER_PAGE) });
        if (action) params.set("action", action);
        if (entityType) params.set("entity_type", entityType);
        const result = await api.get<AuditLogPage>(`/audit?${params.toString()}`);
        setData(result);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Unable to load audit log");
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, [page, action, entityType]);

  const totalPages = data ? Math.ceil(data.total / PER_PAGE) : 1;

  function formatTs(ts: string) {
    return new Date(ts).toLocaleString();
  }

  return (
    <div>
      <Header title="Audit Log" />
      <div className="space-y-4 p-6">
        <div className="flex flex-wrap gap-3">
          <Input
            value={action}
            onChange={(e) => { setAction(e.target.value); setPage(1); }}
            placeholder="Filter by action (e.g. login)"
            className="w-48"
          />
          <Input
            value={entityType}
            onChange={(e) => { setEntityType(e.target.value); setPage(1); }}
            placeholder="Filter by entity type"
            className="w-48"
          />
          {data && (
            <span className="self-center text-sm text-slate-500">{data.total} total entries</span>
          )}
        </div>

        <Card>
          <CardContent className="p-0">
            {loading ? (
              <div className="p-6 text-sm text-slate-500">Loading audit log...</div>
            ) : error ? (
              <div className="p-6 text-sm text-red-600">{error}</div>
            ) : !data || data.entries.length === 0 ? (
              <div className="p-6 text-sm text-slate-500">No audit entries found.</div>
            ) : (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Timestamp</TableHead>
                      <TableHead>Action</TableHead>
                      <TableHead>Entity Type</TableHead>
                      <TableHead>Entity ID</TableHead>
                      <TableHead>Detail</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {data.entries.map((entry) => (
                      <TableRow key={entry.id}>
                        <TableCell className="whitespace-nowrap text-xs text-slate-500">{formatTs(entry.timestamp)}</TableCell>
                        <TableCell>
                          <span className="rounded bg-slate-100 px-2 py-0.5 text-xs font-mono text-slate-700 dark:bg-slate-800 dark:text-slate-300">
                            {entry.action}
                          </span>
                        </TableCell>
                        <TableCell className="text-sm">{entry.entity_type}</TableCell>
                        <TableCell className="font-mono text-xs text-slate-400">{entry.entity_id ? entry.entity_id.slice(0, 8) + "…" : "—"}</TableCell>
                        <TableCell className="max-w-xs truncate text-sm text-slate-600">{entry.detail || "—"}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>

        {totalPages > 1 && (
          <div className="flex items-center gap-2">
            <button
              type="button"
              className="rounded border px-3 py-1 text-sm disabled:opacity-40"
              onClick={() => setPage((p) => p - 1)}
              disabled={page <= 1}
            >
              Previous
            </button>
            <span className="text-sm text-slate-500">Page {page} of {totalPages}</span>
            <button
              type="button"
              className="rounded border px-3 py-1 text-sm disabled:opacity-40"
              onClick={() => setPage((p) => p + 1)}
              disabled={page >= totalPages}
            >
              Next
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
```

---

- [ ] **Step 3: Add "Audit Log" to sidebar**

Add import for `ClipboardList` icon:
```tsx
import { ..., ClipboardList } from "lucide-react";
```

Add to `NAV` array (after "Benchmarks"):
```tsx
{ href: "/admin/audit", label: "Audit Log", icon: ClipboardList, roles: ["it_admin", "district_admin"] },
```

---

- [ ] **Step 4: Build check**

```bash
cd frontend && npm run build 2>&1 | tail -20
```

Expected: Build completes without TypeScript errors.

---

- [ ] **Step 5: Commit**

```bash
git add frontend/src/app/\(protected\)/admin/audit/page.tsx frontend/src/components/layout/sidebar.tsx frontend/src/lib/types.ts && git commit -m "feat: add audit log UI page and sidebar nav entry"
```

---

## SECTION 3 — VISUAL POLISH

---

### Task 7: SubjectBar component and student profile visual upgrade

**Files:**
- Create: `frontend/src/components/students/SubjectBar.tsx`
- Modify: `frontend/src/app/(protected)/students/[id]/page.tsx`

---

- [ ] **Step 1: Create `frontend/src/components/students/SubjectBar.tsx`**

```tsx
"use client";

interface SubjectBarProps {
  subjectName: string;
  average: number;
}

function barColor(score: number): string {
  if (score >= 80) return "bg-green-500";
  if (score >= 70) return "bg-yellow-400";
  return "bg-red-500";
}

function labelColor(score: number): string {
  if (score >= 80) return "text-green-700";
  if (score >= 70) return "text-yellow-700";
  return "text-red-700";
}

export function SubjectBar({ subjectName, average }: SubjectBarProps) {
  const pct = Math.min(Math.max(average, 0), 100);
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-slate-700 dark:text-slate-300">{subjectName}</span>
        <span className={`text-sm font-semibold ${labelColor(average)}`}>{average.toFixed(1)}%</span>
      </div>
      <div className="h-3 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
        <div
          className={`h-full rounded-full transition-all duration-500 ${barColor(average)}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
```

---

- [ ] **Step 2: Update student profile page with subject bars and score color coding**

Replace the entire contents of `frontend/src/app/(protected)/students/[id]/page.tsx` with:

```tsx
"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { AnalysisCard } from "@/components/ai/AnalysisCard";
import { AnalysisHistory } from "@/components/ai/AnalysisHistory";
import { AnalyzeButton } from "@/components/ai/AnalyzeButton";
import { TierBadge } from "@/components/dashboard/TierBadge";
import { InterventionForm } from "@/components/interventions/InterventionForm";
import { InterventionList } from "@/components/interventions/InterventionList";
import { Header } from "@/components/layout/header";
import { SubjectBar } from "@/components/students/SubjectBar";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { AIRecommendation, Intervention, Score, Student, Subject } from "@/lib/types";

function sortInterventions(items: Intervention[]) {
  return [...items].sort((a, b) => {
    if (a.status !== b.status) return a.status.localeCompare(b.status);
    return b.start_date.localeCompare(a.start_date);
  });
}

function scoreCellClass(value: number): string {
  if (value >= 80) return "font-semibold text-green-700 bg-green-50 dark:bg-green-950 dark:text-green-300";
  if (value >= 70) return "font-semibold text-yellow-700 bg-yellow-50 dark:bg-yellow-950 dark:text-yellow-300";
  return "font-semibold text-red-700 bg-red-50 dark:bg-red-950 dark:text-red-300";
}

export default function StudentDetailPage() {
  const params = useParams<{ id: string }>();
  const { user, loading: authLoading } = useAuth();
  const [student, setStudent] = useState<Student | null>(null);
  const [scores, setScores] = useState<Score[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [history, setHistory] = useState<AIRecommendation[]>([]);
  const [interventions, setInterventions] = useState<Intervention[]>([]);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState("");
  const [showInterventionForm, setShowInterventionForm] = useState(false);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError("");
      try {
        const [studentData, scoreData, subjectData, aiHistory, interventionData] = await Promise.all([
          api.get<Student>(`/students/${params.id}`),
          api.get<Score[]>(`/scores/student/${params.id}`),
          api.get<Subject[]>("/lookups/subjects"),
          api.get<AIRecommendation[]>(`/ai/student/${params.id}/history`),
          api.get<Intervention[]>(`/interventions?student_id=${params.id}`),
        ]);
        setStudent(studentData);
        setScores(scoreData);
        setSubjects(subjectData);
        setHistory(aiHistory);
        setInterventions(sortInterventions(interventionData));
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Unable to load student profile");
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, [params.id]);

  async function handleAnalyzeStudent() {
    setAnalyzing(true);
    setError("");
    try {
      const created = await api.post<AIRecommendation>(`/ai/student/${params.id}/analyze`);
      setHistory((current) => [created, ...current]);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unable to analyze student");
    } finally {
      setAnalyzing(false);
    }
  }

  function handleInterventionCreated(intervention: Intervention) {
    setInterventions((current) => sortInterventions([intervention, ...current]));
    setShowInterventionForm(false);
  }

  function handleInterventionUpdated(updated: Intervention) {
    setInterventions((current) =>
      sortInterventions(current.map((i) => (i.id === updated.id ? updated : i)))
    );
  }

  async function handleExport(fmt: "csv" | "pdf") {
    try {
      const res = await fetch(`/api/reports/student/${params.id}?format=${fmt}`, { credentials: "include" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `student_report.${fmt}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Export failed");
    }
  }

  const subjectNames = useMemo(
    () => Object.fromEntries(subjects.map((s) => [s.id, s.name])),
    [subjects]
  );

  // Per-subject averages for SubjectBar
  const subjectAverages = useMemo(() => {
    const grouped: Record<string, number[]> = {};
    for (const score of scores) {
      if (!grouped[score.subject_id]) grouped[score.subject_id] = [];
      grouped[score.subject_id].push(score.value);
    }
    return Object.entries(grouped)
      .map(([subjectId, values]) => ({
        subjectId,
        name: subjectNames[subjectId] ?? subjectId,
        average: values.reduce((a, b) => a + b, 0) / values.length,
      }))
      .sort((a, b) => a.name.localeCompare(b.name));
  }, [scores, subjectNames]);

  // Overall tier for badge
  const overallTier = useMemo(() => {
    if (scores.length === 0) return null;
    const avg = scores.reduce((a, b) => a + b.value, 0) / scores.length;
    if (avg >= 80) return "tier1" as const;
    if (avg >= 70) return "tier2" as const;
    return "tier3" as const;
  }, [scores]);

  return (
    <div>
      <Header title={student ? student.name : "Student Profile"} />
      <div className="space-y-4 p-6">
        <div className="flex flex-wrap items-center gap-2">
          <Link href="/students" className={buttonVariants({ variant: "outline" })}>
            Back to Students
          </Link>
          {student && (
            <div className="flex gap-1">
              <button type="button" className={buttonVariants({ variant: "outline", size: "sm" })} onClick={() => void handleExport("csv")}>
                Export CSV
              </button>
              <button type="button" className={buttonVariants({ variant: "outline", size: "sm" })} onClick={() => void handleExport("pdf")}>
                Export PDF
              </button>
            </div>
          )}
        </div>

        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-24 animate-pulse rounded-lg bg-slate-100 dark:bg-slate-800" />
            ))}
          </div>
        ) : error ? (
          <Card>
            <CardContent className="p-6 text-sm text-red-600">{error}</CardContent>
          </Card>
        ) : student ? (
          <>
            <Card>
              <CardContent className="grid gap-4 p-6 sm:grid-cols-4">
                <div>
                  <p className="text-xs uppercase tracking-wide text-slate-500">Student ID</p>
                  <p className="mt-1 font-medium">{student.student_id_number}</p>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-wide text-slate-500">Grade</p>
                  <p className="mt-1 font-medium">Grade {student.grade_level}</p>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-wide text-slate-500">Scores Recorded</p>
                  <p className="mt-1 font-medium">{scores.length}</p>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-wide text-slate-500">MTSS Tier</p>
                  <div className="mt-1">{overallTier ? <TierBadge tier={overallTier} /> : <span className="text-slate-400 text-sm">No scores</span>}</div>
                </div>
              </CardContent>
            </Card>

            {subjectAverages.length > 0 && (
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base">Subject Performance</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3 p-6 pt-0">
                  {subjectAverages.map((s) => (
                    <SubjectBar key={s.subjectId} subjectName={s.name} average={s.average} />
                  ))}
                </CardContent>
              </Card>
            )}

            <Card>
              <CardContent className="space-y-4 p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">AI Recommendation</p>
                    <p className="text-sm text-slate-500">Generate benchmark-aware support guidance for this student.</p>
                  </div>
                  <AnalyzeButton label="Analyze Student" loading={analyzing} onClick={() => void handleAnalyzeStudent()} />
                </div>
                {history[0] ? <AnalysisCard recommendation={history[0]} /> : null}
                {history.length > 1 && (
                  <div>
                    <p className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-500">History</p>
                    <AnalysisHistory items={history.slice(1)} />
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base">Score History</CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                {scores.length === 0 ? (
                  <div className="p-6 text-sm text-slate-500">No scores recorded for this student yet.</div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Date</TableHead>
                        <TableHead>Subject</TableHead>
                        <TableHead>Type</TableHead>
                        <TableHead>Score</TableHead>
                        <TableHead>Notes</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {scores.map((score) => (
                        <TableRow key={score.id}>
                          <TableCell className="text-sm">{score.date}</TableCell>
                          <TableCell className="text-sm">{subjectNames[score.subject_id] ?? score.subject_id}</TableCell>
                          <TableCell className="capitalize text-sm">{score.score_type}</TableCell>
                          <TableCell className={`rounded-md px-2 py-1 text-sm ${scoreCellClass(score.value)}`}>{score.value}%</TableCell>
                          <TableCell className="text-sm text-slate-500">{score.notes || "—"}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardContent className="space-y-4 p-6">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="text-sm font-medium">Interventions</p>
                    <p className="text-sm text-slate-500">Track active supports and resolution notes for this student.</p>
                  </div>
                  {!authLoading && user ? (
                    <button
                      type="button"
                      className={buttonVariants({ variant: showInterventionForm ? "outline" : "default" })}
                      onClick={() => setShowInterventionForm((current) => !current)}
                    >
                      {showInterventionForm ? "Cancel" : "Add Intervention"}
                    </button>
                  ) : null}
                </div>
                {showInterventionForm && user ? (
                  <div className="rounded-lg border border-slate-200 p-4">
                    <InterventionForm target={{ type: "student", id: params.id }} onCreated={handleInterventionCreated} onCancel={() => setShowInterventionForm(false)} />
                  </div>
                ) : null}
                {user ? (
                  <InterventionList interventions={interventions} userRole={user.role} onUpdated={handleInterventionUpdated} />
                ) : (
                  <p className="text-sm text-slate-500">Loading intervention permissions...</p>
                )}
              </CardContent>
            </Card>
          </>
        ) : null}
      </div>
    </div>
  );
}
```

---

- [ ] **Step 3: Build check**

```bash
cd frontend && npm run build 2>&1 | tail -20
```

Expected: no TypeScript errors.

---

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/students/SubjectBar.tsx frontend/src/app/\(protected\)/students/\[id\]/page.tsx && git commit -m "feat: add SubjectBar component and visual upgrade to student profile"
```

---

### Task 8: Student list tier column and skeleton states

**Files:**
- Modify: `frontend/src/app/(protected)/students/page.tsx`
- Modify: `frontend/src/app/(protected)/dashboard/page.tsx`

---

- [ ] **Step 1: Update `frontend/src/app/(protected)/students/page.tsx`**

Replace the full file contents:

```tsx
"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { TierBadge } from "@/components/dashboard/TierBadge";
import { Header } from "@/components/layout/header";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Class, School, Score, Student } from "@/lib/types";

type TierKey = "tier1" | "tier2" | "tier3";

function computeTier(avg: number): TierKey {
  if (avg >= 80) return "tier1";
  if (avg >= 70) return "tier2";
  return "tier3";
}

export default function StudentsPage() {
  const { user } = useAuth();
  const [students, setStudents] = useState<Student[]>([]);
  const [schools, setSchools] = useState<School[]>([]);
  const [classes, setClasses] = useState<Class[]>([]);
  const [scoreMap, setScoreMap] = useState<Record<string, number>>({});
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError("");
      try {
        const [studentData, schoolData, classData] = await Promise.all([
          api.get<Student[]>("/students"),
          api.get<School[]>("/lookups/schools"),
          api.get<Class[]>("/lookups/classes"),
        ]);
        setStudents(studentData);
        setSchools(schoolData);
        setClasses(classData);

        // Fetch scores for all students to compute tiers
        const scoreResults = await Promise.all(
          studentData.map((s) =>
            api.get<Score[]>(`/scores/student/${s.id}`).then((scores) => ({
              id: s.id,
              avg: scores.length > 0 ? scores.reduce((a, b) => a + b.value, 0) / scores.length : null,
            }))
          )
        );
        const map: Record<string, number> = {};
        for (const r of scoreResults) {
          if (r.avg !== null) map[r.id] = r.avg;
        }
        setScoreMap(map);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Unable to load students");
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, []);

  const schoolNames = useMemo(
    () => Object.fromEntries(schools.map((s) => [s.id, s.name])),
    [schools]
  );
  const classNames = useMemo(
    () => Object.fromEntries(classes.map((c) => [c.id, c.name])),
    [classes]
  );

  const filteredStudents = students.filter((student) => {
    const term = search.trim().toLowerCase();
    if (!term) return true;
    return student.name.toLowerCase().includes(term) || student.student_id_number.toLowerCase().includes(term);
  });

  return (
    <div>
      <Header title="Students" />
      <div className="space-y-4 p-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by student name or ID"
            className="sm:max-w-sm"
          />
          {user && user.role !== "district_admin" ? (
            <Link href="/students/new" className={buttonVariants({ variant: "default" })}>
              Add Student
            </Link>
          ) : null}
        </div>

        <Card>
          <CardContent className="p-0">
            {loading ? (
              <div className="space-y-2 p-4">
                {[1, 2, 3, 4, 5].map((i) => (
                  <div key={i} className="h-10 animate-pulse rounded bg-slate-100 dark:bg-slate-800" />
                ))}
              </div>
            ) : error ? (
              <div className="p-6 text-sm text-red-600">{error}</div>
            ) : filteredStudents.length === 0 ? (
              <div className="p-6 text-center text-sm text-slate-500">
                {search ? `No students matching "${search}".` : "No students found. Add one to get started."}
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Student</TableHead>
                    <TableHead>ID</TableHead>
                    <TableHead>Grade</TableHead>
                    <TableHead>School</TableHead>
                    <TableHead>Class</TableHead>
                    <TableHead>Tier</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredStudents.map((student) => {
                    const avg = scoreMap[student.id];
                    const tier = avg !== undefined ? computeTier(avg) : null;
                    return (
                      <TableRow key={student.id}>
                        <TableCell className="font-medium">
                          <Link href={`/students/${student.id}`} className="hover:underline">
                            {student.name}
                          </Link>
                        </TableCell>
                        <TableCell>{student.student_id_number}</TableCell>
                        <TableCell>Grade {student.grade_level}</TableCell>
                        <TableCell>{schoolNames[student.school_id] ?? student.school_id}</TableCell>
                        <TableCell>{student.class_id ? (classNames[student.class_id] ?? student.class_id) : "Unassigned"}</TableCell>
                        <TableCell>{tier ? <TierBadge tier={tier} /> : <span className="text-xs text-slate-400">No scores</span>}</TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
```

---

- [ ] **Step 2: Add skeleton loading state to dashboard page**

Open `frontend/src/app/(protected)/dashboard/page.tsx`. Replace the loading text `<p>Loading dashboard...</p>` (or equivalent) with:

```tsx
<div className="space-y-4 p-6">
  <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
    {[1, 2, 3].map((i) => (
      <div key={i} className="h-40 animate-pulse rounded-lg bg-slate-100 dark:bg-slate-800" />
    ))}
  </div>
</div>
```

(Read the file first to find the exact loading state to replace.)

---

- [ ] **Step 3: Build check**

```bash
cd frontend && npm run build 2>&1 | tail -20
```

Expected: no TypeScript errors.

---

- [ ] **Step 4: Commit**

```bash
git add frontend/src/app/\(protected\)/students/page.tsx frontend/src/app/\(protected\)/dashboard/page.tsx && git commit -m "feat: add tier column to student list and skeleton loading states"
```

---

### Task 9: Dashboard visual improvements

**Files:**
- Modify: `frontend/src/components/dashboard/TeacherDashboard.tsx`
- Modify: `frontend/src/components/dashboard/PrincipalDashboard.tsx`
- Modify: `frontend/src/components/dashboard/DistrictDashboard.tsx`
- Modify: `frontend/src/components/dashboard/TierBadge.tsx`

---

- [ ] **Step 1: Upgrade TierBadge with stronger color treatment**

Replace the full contents of `frontend/src/components/dashboard/TierBadge.tsx`:

```tsx
"use client";

const TIER_STYLES = {
  tier1: { bg: "bg-green-100 text-green-800 border border-green-300 dark:bg-green-950 dark:text-green-200 dark:border-green-800", label: "Tier 1" },
  tier2: { bg: "bg-yellow-100 text-yellow-800 border border-yellow-300 dark:bg-yellow-950 dark:text-yellow-200 dark:border-yellow-800", label: "Tier 2" },
  tier3: { bg: "bg-red-100 text-red-800 border border-red-300 dark:bg-red-950 dark:text-red-200 dark:border-red-800", label: "Tier 3" },
} as const;

interface TierBadgeProps {
  tier: "tier1" | "tier2" | "tier3";
}

export function TierBadge({ tier }: TierBadgeProps) {
  const { bg, label } = TIER_STYLES[tier];
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${bg}`}>
      {label}
    </span>
  );
}
```

---

- [ ] **Step 2: Update at-risk table rows in TeacherDashboard for stronger highlighting**

In `frontend/src/components/dashboard/TeacherDashboard.tsx`, update the `TableRow` className for at-risk students. Replace the existing ternary with:

```tsx
className={
  student.tier === "tier3"
    ? "bg-red-50 dark:bg-red-950/30 border-l-2 border-l-red-500"
    : student.tier === "tier2"
    ? "bg-yellow-50 dark:bg-yellow-950/30 border-l-2 border-l-yellow-400"
    : undefined
}
```

Also update the avg score cell to use color coding:

Replace `<TableCell>{student.avg_score.toFixed(1)}</TableCell>` with:
```tsx
<TableCell>
  <span className={`rounded px-2 py-0.5 text-sm font-semibold ${
    student.tier === "tier1" ? "text-green-700 bg-green-50" :
    student.tier === "tier2" ? "text-yellow-700 bg-yellow-50" :
    "text-red-700 bg-red-50"
  }`}>
    {student.avg_score.toFixed(1)}%
  </span>
</TableCell>
```

---

- [ ] **Step 3: Apply same row treatment to PrincipalDashboard and DistrictDashboard**

Open each file and apply the same at-risk `TableRow` className pattern from Step 2 to their at-risk tables. Also update any avg_score display cells to use the same color span pattern.

(Read each file first to locate the exact at-risk table rows before editing.)

---

- [ ] **Step 4: Final build check**

```bash
cd frontend && npm run build 2>&1 | tail -30
```

Expected: clean build, no errors.

---

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/dashboard/ && git commit -m "feat: visual polish for tier badges and dashboard at-risk highlighting"
```

---

## End of Plan

After each section is implemented, tested with agent-browser, and passes: push to GitHub with `git push origin main`.

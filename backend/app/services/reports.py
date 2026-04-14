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
    students = db.query(Student).filter(Student.class_id.in_(class_ids)).all() if class_ids else []

    scores_map: dict = defaultdict(list)
    if students:
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
        if scores_map.get(s.id) and calculate_tier(
            sum(scores_map[s.id]) / len(scores_map[s.id])
        ).value in ("tier2", "tier3")
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
        return {
            "student_count": 0,
            "avg_score": None,
            "tier_distribution": {"tier1": 0, "tier2": 0, "tier3": 0},
            "high_risk": False,
        }
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
        w.writerow([
            row.student_name,
            f"{row.avg_score:.1f}" if row.avg_score is not None else "—",
            row.tier or "—",
        ])
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
            cls.tier_distribution["tier1"],
            cls.tier_distribution["tier2"],
            cls.tier_distribution["tier3"],
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
            school.tier_distribution["tier1"],
            school.tier_distribution["tier2"],
            school.tier_distribution["tier3"],
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
    pdf = _base_pdf(f"Student Report - {data.student_name}")
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
        _pdf_table_row(pdf, [
            (s.subject_name, 70),
            (f"{s.average:.1f}", 40),
            (s.tier.replace("tier", "Tier "), 40),
        ])
    if data.latest_ai_recommendation:
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, "Latest AI Recommendation", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(0, 5, data.latest_ai_recommendation)
    return bytes(pdf.output())


def to_pdf_class(data: ClassReportData) -> bytes:
    pdf = _base_pdf(f"Class Report - {data.class_name}")
    _pdf_row(pdf, "Grade", str(data.grade_level))
    _pdf_row(pdf, "School", data.school_name)
    _pdf_row(pdf, "Students", str(data.student_count))
    _pdf_row(pdf, "Tier 1 / 2 / 3", (
        f"{data.tier_distribution['tier1']} / "
        f"{data.tier_distribution['tier2']} / "
        f"{data.tier_distribution['tier3']}"
    ))
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
    pdf = _base_pdf(f"School Report - {data.school_name}")
    _pdf_row(pdf, "Total Students", str(data.total_students))
    _pdf_row(pdf, "At-Risk Students", str(data.at_risk_count))
    pdf.ln(4)
    _pdf_table_header(pdf, [
        ("Class", 55), ("Gr", 12), ("Students", 25), ("Avg", 20),
        ("T1", 18), ("T2", 18), ("T3", 18),
    ])
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
            _pdf_table_row(pdf, [
                (str(g["grade_level"]), 40),
                (str(g["avg_score"]), 50),
                (str(g["student_count"]), 50),
            ])
    return bytes(pdf.output())


def to_pdf_district(data: DistrictReportData) -> bytes:
    pdf = _base_pdf("District Report")
    _pdf_row(pdf, "Total Students", str(data.total_students))
    _pdf_row(pdf, "Tier 1 / 2 / 3", (
        f"{data.tier_distribution['tier1']} / "
        f"{data.tier_distribution['tier2']} / "
        f"{data.tier_distribution['tier3']}"
    ))
    pdf.ln(4)
    _pdf_table_header(pdf, [
        ("School", 65), ("Students", 25), ("Avg", 20),
        ("T1", 18), ("T2", 18), ("T3", 18), ("Risk", 18),
    ])
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

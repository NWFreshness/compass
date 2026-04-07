import csv
import io
from datetime import date
from sqlalchemy.orm import Session
from app.models import Student, Subject, Score, ScoreType
from app.schemas.score import CSVImportResult, CSVRowError

REQUIRED_COLUMNS = {"student_id_number", "subject_name", "score_type", "value", "date"}


def parse_and_validate_csv(db: Session, file_bytes: bytes) -> CSVImportResult:
    text = file_bytes.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    if not REQUIRED_COLUMNS.issubset(set(reader.fieldnames or [])):
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        return CSVImportResult(imported=0, errors=[CSVRowError(row=0, message=f"Missing columns: {missing}")])

    scores_to_add: list[Score] = []
    errors: list[CSVRowError] = []

    for i, row in enumerate(reader, start=2):
        row_errors = []

        student = db.query(Student).filter(Student.student_id_number == row["student_id_number"].strip()).first()
        if not student:
            row_errors.append(f"Student '{row['student_id_number']}' not found")

        subject = db.query(Subject).filter(Subject.name == row["subject_name"].strip()).first()
        if not subject:
            row_errors.append(f"Subject '{row['subject_name']}' not found")

        score_type = None
        try:
            score_type = ScoreType(row["score_type"].strip().lower())
        except ValueError:
            row_errors.append(f"Invalid score_type '{row['score_type']}' (must be homework, quiz, or test)")

        value = None
        try:
            value = float(row["value"])
        except ValueError:
            row_errors.append(f"Invalid value '{row['value']}' (must be a number)")
        else:
            if not (0 <= value <= 100):
                row_errors.append(f"Value '{row['value']}' out of range (must be 0-100)")
                value = None

        score_date = None
        try:
            score_date = date.fromisoformat(row["date"].strip())
        except ValueError:
            row_errors.append(f"Invalid date '{row['date']}' (must be YYYY-MM-DD)")

        if row_errors:
            errors.append(CSVRowError(row=i, message="; ".join(row_errors)))
        elif student and subject and score_type is not None and value is not None and score_date:
            scores_to_add.append(Score(
                student_id=student.id,
                subject_id=subject.id,
                score_type=score_type,
                value=value,
                date=score_date,
                notes=row.get("notes", "").strip() or None,
            ))

    if not errors and scores_to_add:
        db.add_all(scores_to_add)
        db.commit()

    return CSVImportResult(imported=len(scores_to_add) if not errors else 0, errors=errors)

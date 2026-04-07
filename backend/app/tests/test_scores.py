import io
import csv
from app.services.auth import hash_password
from app.models import User, UserRole, School, Class, Student, Subject


def seed_score_world(db):
    school = School(name="Score School")
    db.add(school)
    db.flush()
    teacher = User(username="teacher", hashed_password=hash_password("password1"), role=UserRole.teacher, school_id=school.id)
    db.add(teacher)
    db.flush()
    cls = Class(name="4B", grade_level=4, school_id=school.id, teacher_id=teacher.id)
    db.add(cls)
    db.flush()
    student = Student(name="Carlos", student_id_number="S100", grade_level=4, school_id=school.id, class_id=cls.id)
    subject = Subject(name="Reading")
    db.add_all([student, subject])
    db.commit()
    return {"teacher": teacher, "student": student, "subject": subject}


def test_create_single_score(client, db):
    w = seed_score_world(db)
    assert client.post("/api/auth/login", json={"username": "teacher", "password": "password1"}).status_code == 200
    res = client.post("/api/scores", json={
        "student_id": str(w["student"].id),
        "subject_id": str(w["subject"].id),
        "score_type": "quiz",
        "value": 85.0,
        "date": "2026-03-01",
    })
    assert res.status_code == 201
    assert res.json()["value"] == 85.0


def test_get_scores_for_student(client, db):
    w = seed_score_world(db)
    assert client.post("/api/auth/login", json={"username": "teacher", "password": "password1"}).status_code == 200
    # Insert two scores with different dates to verify ordering
    client.post("/api/scores", json={
        "student_id": str(w["student"].id),
        "subject_id": str(w["subject"].id),
        "score_type": "test",
        "value": 90.0,
        "date": "2026-03-01",
    })
    client.post("/api/scores", json={
        "student_id": str(w["student"].id),
        "subject_id": str(w["subject"].id),
        "score_type": "quiz",
        "value": 75.0,
        "date": "2026-03-15",
    })
    res = client.get(f"/api/scores/student/{w['student'].id}")
    assert res.status_code == 200
    scores = res.json()
    assert len(scores) == 2
    # Most recent date should come first (ordered by date desc)
    assert scores[0]["date"] > scores[1]["date"]


def test_csv_import_valid(client, db):
    w = seed_score_world(db)
    assert client.post("/api/auth/login", json={"username": "teacher", "password": "password1"}).status_code == 200
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["student_id_number", "subject_name", "score_type", "value", "date", "notes"])
    writer.writerow(["S100", "Reading", "homework", "78", "2026-03-10", "good effort"])
    res = client.post("/api/scores/import", files={"file": ("scores.csv", buf.getvalue().encode(), "text/csv")})
    assert res.status_code == 200
    assert res.json()["imported"] == 1
    assert res.json()["errors"] == []


def test_csv_import_invalid_score_type(client, db):
    w = seed_score_world(db)
    assert client.post("/api/auth/login", json={"username": "teacher", "password": "password1"}).status_code == 200
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["student_id_number", "subject_name", "score_type", "value", "date", "notes"])
    writer.writerow(["S100", "Reading", "BADTYPE", "78", "2026-03-10", ""])
    res = client.post("/api/scores/import", files={"file": ("scores.csv", buf.getvalue().encode(), "text/csv")})
    assert res.status_code == 200
    assert res.json()["imported"] == 0
    assert len(res.json()["errors"]) == 1


def test_csv_template_download(client, db):
    w = seed_score_world(db)
    assert client.post("/api/auth/login", json={"username": "teacher", "password": "password1"}).status_code == 200
    res = client.get("/api/scores/template.csv")
    assert res.status_code == 200
    assert "student_id_number" in res.text

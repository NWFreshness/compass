"""Idempotent seed script. Run with: uv run python -m app.seed"""
import random
from datetime import date, timedelta
from app.db import SessionLocal
from app.models import User, UserRole, School, Class, Student, Subject, Score, ScoreType
from app.services.auth import hash_password


def seed():
    db = SessionLocal()
    try:
        if db.query(User).filter(User.username == "admin").first():
            print("Database already seeded. Skipping.")
            return

        # Schools
        school1 = School(name="Lincoln Elementary", address="100 Lincoln Ave")
        school2 = School(name="Washington Middle School", address="200 Washington Blvd")
        db.add_all([school1, school2])
        db.flush()

        # Users (one per role)
        admin = User(username="admin", hashed_password=hash_password("changeme"), role=UserRole.it_admin)
        district = User(username="district", hashed_password=hash_password("changeme"), role=UserRole.district_admin)
        principal = User(username="principal", hashed_password=hash_password("changeme"), role=UserRole.principal, school_id=school1.id)
        teacher = User(username="teacher", hashed_password=hash_password("changeme"), role=UserRole.teacher, school_id=school1.id)
        db.add_all([admin, district, principal, teacher])
        db.flush()

        # Classes
        class1 = Class(name="Grade 5 - Room A", grade_level=5, school_id=school1.id, teacher_id=teacher.id)
        class2 = Class(name="Grade 4 - Room B", grade_level=4, school_id=school1.id, teacher_id=teacher.id)
        db.add_all([class1, class2])
        db.flush()

        # Subjects
        math = Subject(name="Mathematics")
        reading = Subject(name="Reading")
        science = Subject(name="Science")
        db.add_all([math, reading, science])
        db.flush()

        # Students (10 total)
        student_data = [
            ("Alice Johnson", "S001", 5, class1.id),
            ("Bob Martinez", "S002", 5, class1.id),
            ("Carol White", "S003", 5, class1.id),
            ("David Lee", "S004", 5, class1.id),
            ("Emma Davis", "S005", 5, class1.id),
            ("Frank Wilson", "S006", 4, class2.id),
            ("Grace Taylor", "S007", 4, class2.id),
            ("Henry Anderson", "S008", 4, class2.id),
            ("Isabella Thomas", "S009", 4, class2.id),
            ("James Jackson", "S010", 4, class2.id),
        ]
        students = []
        for name, sid, grade, cls_id in student_data:
            s = Student(name=name, student_id_number=sid, grade_level=grade, school_id=school1.id, class_id=cls_id)
            db.add(s)
            students.append(s)
        db.flush()

        # Scores (~90 spread across students/subjects/dates)
        subjects = [math, reading, science]
        score_types = list(ScoreType)
        base_date = date.today() - timedelta(days=60)
        rng = random.Random(42)
        for student in students:
            for subject in subjects:
                for _ in range(3):
                    score = Score(
                        student_id=student.id,
                        subject_id=subject.id,
                        score_type=rng.choice(score_types),
                        value=round(rng.uniform(55, 98), 1),
                        date=base_date + timedelta(days=rng.randint(0, 55)),
                    )
                    db.add(score)

        db.commit()
        print("Seed complete.")
        print("  Users: admin, district, principal, teacher (all password: changeme)")
        print("  Schools: 2 | Classes: 2 | Students: 10 | Subjects: 3 | Scores: 90")
    finally:
        db.close()


if __name__ == "__main__":
    seed()

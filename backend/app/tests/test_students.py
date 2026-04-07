from app.services.auth import hash_password
from app.models import User, UserRole, School, Class, Student


def seed_world(db):
    school = School(name="Test School")
    db.add(school)
    db.flush()
    teacher = User(username="teacher", hashed_password=hash_password("password1"), role=UserRole.teacher, school_id=school.id)
    admin = User(username="admin", hashed_password=hash_password("password1"), role=UserRole.it_admin)
    db.add_all([teacher, admin])
    db.flush()
    cls = Class(name="5A", grade_level=5, school_id=school.id, teacher_id=teacher.id)
    db.add(cls)
    db.flush()
    student = Student(name="Alice Smith", student_id_number="S001", grade_level=5, school_id=school.id, class_id=cls.id)
    db.add(student)
    db.commit()
    return {"school": school, "teacher": teacher, "admin": admin, "class": cls, "student": student}


def test_admin_can_list_all_students(client, db):
    w = seed_world(db)
    client.post("/api/auth/login", json={"username": "admin", "password": "password1"})
    res = client.get("/api/students")
    assert res.status_code == 200
    assert len(res.json()) >= 1


def test_teacher_sees_own_class_students(client, db):
    w = seed_world(db)
    client.post("/api/auth/login", json={"username": "teacher", "password": "password1"})
    res = client.get("/api/students")
    assert res.status_code == 200
    ids = [s["student_id_number"] for s in res.json()]
    assert "S001" in ids


def test_get_student_by_id(client, db):
    w = seed_world(db)
    client.post("/api/auth/login", json={"username": "admin", "password": "password1"})
    sid = str(w["student"].id)
    res = client.get(f"/api/students/{sid}")
    assert res.status_code == 200
    assert res.json()["name"] == "Alice Smith"


def test_create_student(client, db):
    w = seed_world(db)
    client.post("/api/auth/login", json={"username": "admin", "password": "password1"})
    res = client.post("/api/students", json={
        "name": "Bob Jones", "student_id_number": "S002",
        "grade_level": 5, "school_id": str(w["school"].id),
        "class_id": str(w["class"].id),
    })
    assert res.status_code == 201
    assert res.json()["name"] == "Bob Jones"


def test_patch_student(client, db):
    w = seed_world(db)
    client.post("/api/auth/login", json={"username": "admin", "password": "password1"})
    sid = str(w["student"].id)
    res = client.patch(f"/api/students/{sid}", json={"name": "Alice Updated"})
    assert res.status_code == 200
    assert res.json()["name"] == "Alice Updated"


def test_unauthenticated_cannot_list_students(client, db):
    res = client.get("/api/students")
    assert res.status_code == 401

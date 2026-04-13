from datetime import date
from app.services.auth import hash_password
from app.models import User, UserRole, School, Class, Student, Intervention, InterventionStatus


def seed_world(db):
    school = School(name="Test School")
    db.add(school)
    db.flush()
    teacher = User(username="teacher", hashed_password=hash_password("pw"), role=UserRole.teacher, school_id=school.id)
    principal = User(username="principal", hashed_password=hash_password("pw"), role=UserRole.principal, school_id=school.id)
    admin = User(username="admin", hashed_password=hash_password("pw"), role=UserRole.it_admin)
    db.add_all([teacher, principal, admin])
    db.flush()
    cls = Class(name="5A", grade_level=5, school_id=school.id, teacher_id=teacher.id)
    db.add(cls)
    db.flush()
    student = Student(name="Alice", student_id_number="S001", grade_level=5, school_id=school.id, class_id=cls.id)
    db.add(student)
    db.commit()
    return {"school": school, "teacher": teacher, "principal": principal, "admin": admin, "class": cls, "student": student}


START = str(date.today())


def login(client, username):
    assert client.post("/api/auth/login", json={"username": username, "password": "pw"}).status_code == 200


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

def test_admin_create_student_intervention(client, db):
    w = seed_world(db)
    login(client, "admin")
    res = client.post("/api/interventions", json={
        "student_id": str(w["student"].id),
        "strategy": "Tier 2 reading support",
        "start_date": START,
    })
    assert res.status_code == 201
    data = res.json()
    assert data["student_id"] == str(w["student"].id)
    assert data["class_id"] is None
    assert data["status"] == "active"


def test_admin_create_class_intervention(client, db):
    w = seed_world(db)
    login(client, "admin")
    res = client.post("/api/interventions", json={
        "class_id": str(w["class"].id),
        "strategy": "Whole-class math support",
        "start_date": START,
    })
    assert res.status_code == 201
    assert res.json()["class_id"] == str(w["class"].id)
    assert res.json()["student_id"] is None


def test_reject_both_targets(client, db):
    w = seed_world(db)
    login(client, "admin")
    res = client.post("/api/interventions", json={
        "student_id": str(w["student"].id),
        "class_id": str(w["class"].id),
        "strategy": "Overlap",
        "start_date": START,
    })
    assert res.status_code == 422


def test_reject_no_target(client, db):
    w = seed_world(db)
    login(client, "admin")
    res = client.post("/api/interventions", json={
        "strategy": "No target",
        "start_date": START,
    })
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# Scope enforcement
# ---------------------------------------------------------------------------

def test_teacher_can_create_for_own_student(client, db):
    w = seed_world(db)
    login(client, "teacher")
    res = client.post("/api/interventions", json={
        "student_id": str(w["student"].id),
        "strategy": "Reading support",
        "start_date": START,
    })
    assert res.status_code == 201


def test_teacher_cannot_create_for_outside_student(client, db):
    w = seed_world(db)
    other_school = School(name="Other School")
    db.add(other_school)
    db.flush()
    other_cls = Class(name="6B", grade_level=6, school_id=other_school.id)
    db.add(other_cls)
    db.flush()
    other_student = Student(name="Bob", student_id_number="S999", grade_level=6, school_id=other_school.id, class_id=other_cls.id)
    db.add(other_student)
    db.commit()
    login(client, "teacher")
    res = client.post("/api/interventions", json={
        "student_id": str(other_student.id),
        "strategy": "Interloper",
        "start_date": START,
    })
    assert res.status_code == 403


def test_principal_can_create_for_school_class(client, db):
    w = seed_world(db)
    login(client, "principal")
    res = client.post("/api/interventions", json={
        "class_id": str(w["class"].id),
        "strategy": "Class support",
        "start_date": START,
    })
    assert res.status_code == 201


# ---------------------------------------------------------------------------
# Patch
# ---------------------------------------------------------------------------

def test_patch_status_and_outcome(client, db):
    w = seed_world(db)
    login(client, "admin")
    create_res = client.post("/api/interventions", json={
        "student_id": str(w["student"].id),
        "strategy": "Support plan",
        "start_date": START,
    })
    iid = create_res.json()["id"]
    patch_res = client.patch(f"/api/interventions/{iid}", json={
        "status": "resolved",
        "outcome_notes": "Student improved significantly",
    })
    assert patch_res.status_code == 200
    data = patch_res.json()
    assert data["status"] == "resolved"
    assert data["outcome_notes"] == "Student improved significantly"


def test_patch_404(client, db):
    seed_world(db)
    login(client, "admin")
    import uuid
    res = client.patch(f"/api/interventions/{uuid.uuid4()}", json={"status": "resolved"})
    assert res.status_code == 404


# ---------------------------------------------------------------------------
# List filtering
# ---------------------------------------------------------------------------

def test_list_by_student_id(client, db):
    w = seed_world(db)
    login(client, "admin")
    client.post("/api/interventions", json={"student_id": str(w["student"].id), "strategy": "A", "start_date": START})
    client.post("/api/interventions", json={"class_id": str(w["class"].id), "strategy": "B", "start_date": START})
    res = client.get(f"/api/interventions?student_id={w['student'].id}")
    assert res.status_code == 200
    results = res.json()
    assert all(r["student_id"] == str(w["student"].id) for r in results)


def test_list_by_class_id(client, db):
    w = seed_world(db)
    login(client, "admin")
    client.post("/api/interventions", json={"student_id": str(w["student"].id), "strategy": "A", "start_date": START})
    client.post("/api/interventions", json={"class_id": str(w["class"].id), "strategy": "B", "start_date": START})
    res = client.get(f"/api/interventions?class_id={w['class'].id}")
    assert res.status_code == 200
    results = res.json()
    assert all(r["class_id"] == str(w["class"].id) for r in results)


def test_list_by_status(client, db):
    w = seed_world(db)
    login(client, "admin")
    r1 = client.post("/api/interventions", json={"student_id": str(w["student"].id), "strategy": "A", "start_date": START})
    iid = r1.json()["id"]
    client.patch(f"/api/interventions/{iid}", json={"status": "resolved"})
    client.post("/api/interventions", json={"student_id": str(w["student"].id), "strategy": "B", "start_date": START})

    active = client.get("/api/interventions?status=active").json()
    resolved = client.get("/api/interventions?status=resolved").json()
    assert all(r["status"] == "active" for r in active)
    assert all(r["status"] == "resolved" for r in resolved)


def test_unauthenticated_cannot_list(client, db):
    res = client.get("/api/interventions")
    assert res.status_code == 401

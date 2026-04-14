import uuid
import pytest
from app.models import AuditLog, School, User, UserRole
from app.services.audit import log_action
from app.services.auth import hash_password


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
    assert data["total"] >= 3


def test_district_admin_sees_only_own_school_entries(client, db):
    world = seed_audit_world(db)
    login_as(client, "audit_district")
    r = client.get("/api/audit")
    assert r.status_code == 200
    data = r.json()
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

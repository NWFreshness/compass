import pytest
from app.services.auth import hash_password
from app.models import User, UserRole, School


def make_admin(db):
    u = User(username="admin", hashed_password=hash_password("pass"), role=UserRole.it_admin)
    db.add(u)
    db.commit()
    return u


def make_teacher(db):
    u = User(username="teacher1", hashed_password=hash_password("pass"), role=UserRole.teacher)
    db.add(u)
    db.commit()
    return u


def admin_client(client, db):
    make_admin(db)
    client.post("/api/auth/login", json={"username": "admin", "password": "pass"})
    return client


def test_list_users_as_admin(client, db):
    c = admin_client(client, db)
    res = c.get("/api/admin/users")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_list_users_as_teacher_forbidden(client, db):
    make_teacher(db)
    client.post("/api/auth/login", json={"username": "teacher1", "password": "pass"})
    res = client.get("/api/admin/users")
    assert res.status_code == 403


def test_create_user(client, db):
    c = admin_client(client, db)
    res = c.post("/api/admin/users", json={"username": "newuser", "password": "pass1234", "role": "teacher"})
    assert res.status_code == 201
    assert res.json()["username"] == "newuser"


def test_create_duplicate_user(client, db):
    c = admin_client(client, db)
    c.post("/api/admin/users", json={"username": "dup", "password": "password1", "role": "teacher"})
    res = c.post("/api/admin/users", json={"username": "dup", "password": "password1", "role": "teacher"})
    assert res.status_code == 409


def test_create_school(client, db):
    c = admin_client(client, db)
    res = c.post("/api/admin/schools", json={"name": "Lincoln Elementary", "address": "123 Main St"})
    assert res.status_code == 201
    assert res.json()["name"] == "Lincoln Elementary"


def test_create_subject(client, db):
    c = admin_client(client, db)
    res = c.post("/api/admin/subjects", json={"name": "Mathematics"})
    assert res.status_code == 201


def test_delete_user(client, db):
    c = admin_client(client, db)
    r = c.post("/api/admin/users", json={"username": "todel", "password": "password1", "role": "teacher"})
    uid = r.json()["id"]
    res = c.delete(f"/api/admin/users/{uid}")
    assert res.status_code == 204

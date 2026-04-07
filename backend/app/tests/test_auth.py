from app.services.auth import hash_password
from app.models import User, UserRole


def seed_admin(db):
    user = User(username="admin", hashed_password=hash_password("secret"), role=UserRole.it_admin)
    db.add(user)
    db.commit()
    return user


def test_login_success(client, db):
    seed_admin(db)
    res = client.post("/api/auth/login", json={"username": "admin", "password": "secret"})
    assert res.status_code == 200
    assert res.json()["username"] == "admin"
    assert "session_id" in res.cookies


def test_login_wrong_password(client, db):
    seed_admin(db)
    res = client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
    assert res.status_code == 401


def test_login_unknown_user(client, db):
    res = client.post("/api/auth/login", json={"username": "nobody", "password": "x"})
    assert res.status_code == 401


def test_me_authenticated(client, db):
    seed_admin(db)
    client.post("/api/auth/login", json={"username": "admin", "password": "secret"})
    res = client.get("/api/auth/me")
    assert res.status_code == 200
    assert res.json()["role"] == "it_admin"


def test_me_unauthenticated(client, db):
    res = client.get("/api/auth/me")
    assert res.status_code == 401


def test_logout(client, db):
    seed_admin(db)
    client.post("/api/auth/login", json={"username": "admin", "password": "secret"})
    client.post("/api/auth/logout")
    res = client.get("/api/auth/me")
    assert res.status_code == 401

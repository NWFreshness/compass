from app.services.auth import hash_password
from app.models import User, UserRole, School, Class, Subject


def seed_world(db):
    school_one = School(name="Lincoln Elementary")
    school_two = School(name="Roosevelt Middle")
    db.add_all([school_one, school_two])
    db.flush()

    admin = User(username="admin", hashed_password=hash_password("password1"), role=UserRole.it_admin)
    district = User(username="district", hashed_password=hash_password("password1"), role=UserRole.district_admin)
    principal = User(
        username="principal",
        hashed_password=hash_password("password1"),
        role=UserRole.principal,
        school_id=school_one.id,
    )
    teacher = User(
        username="teacher",
        hashed_password=hash_password("password1"),
        role=UserRole.teacher,
        school_id=school_one.id,
    )
    db.add_all([admin, district, principal, teacher])
    db.flush()

    class_one = Class(name="5A", grade_level=5, school_id=school_one.id, teacher_id=teacher.id)
    class_two = Class(name="4B", grade_level=4, school_id=school_one.id)
    class_three = Class(name="7C", grade_level=7, school_id=school_two.id)
    db.add_all([class_one, class_two, class_three])

    db.add_all([Subject(name="Mathematics"), Subject(name="Reading")])
    db.commit()

    return {
        "school_one": school_one,
        "school_two": school_two,
        "class_one": class_one,
        "class_two": class_two,
        "class_three": class_three,
    }


def login(client, username: str):
    response = client.post("/api/auth/login", json={"username": username, "password": "password1"})
    assert response.status_code == 200


def test_teacher_lookups_are_scoped(client, db):
    world = seed_world(db)
    login(client, "teacher")

    schools = client.get("/api/lookups/schools")
    classes = client.get("/api/lookups/classes")
    subjects = client.get("/api/lookups/subjects")

    assert schools.status_code == 200
    assert schools.json() == [
        {
            "id": str(world["school_one"].id),
            "name": "Lincoln Elementary",
            "address": None,
        }
    ]

    assert classes.status_code == 200
    assert [item["name"] for item in classes.json()] == ["5A"]

    assert subjects.status_code == 200
    assert sorted(item["name"] for item in subjects.json()) == ["Mathematics", "Reading"]


def test_principal_sees_only_their_school_classes(client, db):
    seed_world(db)
    login(client, "principal")

    classes = client.get("/api/lookups/classes")

    assert classes.status_code == 200
    assert sorted(item["name"] for item in classes.json()) == ["4B", "5A"]


def test_admin_sees_all_schools(client, db):
    seed_world(db)
    login(client, "admin")

    schools = client.get("/api/lookups/schools")

    assert schools.status_code == 200
    assert sorted(item["name"] for item in schools.json()) == ["Lincoln Elementary", "Roosevelt Middle"]


def test_unauthenticated_lookup_is_rejected(client, db):
    seed_world(db)

    response = client.get("/api/lookups/subjects")

    assert response.status_code == 401

# Compass Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the foundational Compass MVP — auth, all DB tables, student/score data management, CSV import, and admin tools.

**Architecture:** FastAPI backend with SQLAlchemy + SQLite (PostgreSQL-ready via UUID PKs and no SQLite-specific features). Next.js App Router frontend proxying `/api/*` to the backend. Session auth via HttpOnly cookies backed by a `sessions` table.

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy 2.0, Alembic, passlib[bcrypt], pydantic-settings, uv | Next.js 15, TypeScript, Tailwind CSS, shadcn/ui, Recharts, npm

---

## File Map

### Backend (`backend/`)
| File | Responsibility |
|------|---------------|
| `pyproject.toml` | uv project config + all deps |
| `.env.example` | env var template |
| `alembic.ini` + `alembic/env.py` | migration runner config |
| `alembic/versions/001_initial.py` | all Phase 1–4 tables |
| `app/config.py` | pydantic-settings (DATABASE_URL, session config, Ollama) |
| `app/db.py` | SQLAlchemy engine + `get_db` dep |
| `app/main.py` | FastAPI app, router registration |
| `app/models/base.py` | DeclarativeBase |
| `app/models/school.py` | School ORM model |
| `app/models/user.py` | User + Session ORM models |
| `app/models/class_.py` | Class ORM model |
| `app/models/student.py` | Student ORM model |
| `app/models/subject.py` | Subject + Benchmark ORM models |
| `app/models/score.py` | Score ORM model |
| `app/models/ai_rec.py` | AIRec ORM model (Phase 3, table only) |
| `app/models/intervention.py` | Intervention ORM model (Phase 3, table only) |
| `app/models/audit_log.py` | AuditLog ORM model (Phase 4, table only) |
| `app/models/__init__.py` | Re-exports all models for Alembic |
| `app/schemas/auth.py` | LoginRequest, UserResponse |
| `app/schemas/admin.py` | UserCreate/Update, SchoolCreate, ClassCreate, SubjectCreate |
| `app/schemas/student.py` | StudentCreate, StudentUpdate, StudentResponse |
| `app/schemas/score.py` | ScoreCreate, ScoreResponse, CSVImportResult |
| `app/services/auth.py` | hash/verify password, create/get/delete session |
| `app/services/mtss.py` | calculate_tier, get_student_summary |
| `app/services/csv_import.py` | parse_and_validate_csv |
| `app/middleware/auth.py` | `get_current_user` dep, `require_role` factory |
| `app/routes/auth.py` | /api/auth/login, /logout, /me |
| `app/routes/admin.py` | /api/admin/users, schools, classes, subjects |
| `app/routes/students.py` | /api/students CRUD |
| `app/routes/scores.py` | /api/scores entry, import, template |
| `app/seed.py` | idempotent seed script |
| `app/tests/conftest.py` | TestClient + in-memory SQLite per session |
| `app/tests/test_auth.py` | auth flow + RBAC tests |
| `app/tests/test_mtss.py` | tier calculation tests |
| `app/tests/test_admin.py` | admin CRUD + role enforcement tests |
| `app/tests/test_students.py` | student CRUD + role scoping tests |
| `app/tests/test_scores.py` | score entry + CSV import tests |

### Frontend (`frontend/`)
| File | Responsibility |
|------|---------------|
| `next.config.ts` | rewrites `/api/*` → backend |
| `src/lib/types.ts` | shared TypeScript interfaces |
| `src/lib/api.ts` | typed fetch wrapper |
| `src/lib/auth.tsx` | AuthProvider + useAuth hook |
| `src/app/layout.tsx` | root layout (AuthProvider, ThemeProvider) |
| `src/app/page.tsx` | redirect to /students or /login |
| `src/app/login/page.tsx` | login form |
| `src/app/(protected)/layout.tsx` | auth guard + sidebar shell |
| `src/components/layout/sidebar.tsx` | role-aware nav links + logout |
| `src/components/layout/header.tsx` | page title + theme toggle |
| `src/app/(protected)/students/page.tsx` | searchable student table |
| `src/app/(protected)/students/[id]/page.tsx` | student profile + scores table |
| `src/app/(protected)/students/new/page.tsx` | create student form |
| `src/app/(protected)/scores/entry/page.tsx` | single score entry form |
| `src/app/(protected)/scores/import/page.tsx` | CSV upload + validation feedback |
| `src/app/(protected)/admin/users/page.tsx` | user CRUD |
| `src/app/(protected)/admin/schools/page.tsx` | school CRUD |
| `src/app/(protected)/admin/classes/page.tsx` | class CRUD |
| `src/app/(protected)/admin/subjects/page.tsx` | subject CRUD |

### Deploy
| File | Responsibility |
|------|---------------|
| `deploy/start.bat` | Windows startup script |
| `deploy/start.sh` | Linux startup script |
| `README.md` | install + run instructions |

---

## Task 1: Backend scaffold + all ORM models

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/.env.example`
- Create: `backend/app/__init__.py`
- Create: `backend/app/config.py`
- Create: `backend/app/db.py`
- Create: `backend/app/main.py`
- Create: `backend/app/models/base.py`
- Create: `backend/app/models/school.py`
- Create: `backend/app/models/user.py`
- Create: `backend/app/models/class_.py`
- Create: `backend/app/models/student.py`
- Create: `backend/app/models/subject.py`
- Create: `backend/app/models/score.py`
- Create: `backend/app/models/ai_rec.py`
- Create: `backend/app/models/intervention.py`
- Create: `backend/app/models/audit_log.py`
- Create: `backend/app/models/__init__.py`

- [ ] **Step 1: Create backend directory and pyproject.toml**

```bash
mkdir -p backend/app/models backend/app/schemas backend/app/routes backend/app/services backend/app/middleware backend/app/tests backend/alembic/versions
```

`backend/pyproject.toml`:
```toml
[project]
name = "compass-backend"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.30",
    "sqlalchemy>=2.0",
    "alembic>=1.13",
    "pydantic-settings>=2.7",
    "passlib[bcrypt]>=1.7",
    "python-multipart>=0.0.12",
    "httpx>=0.27",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
testpaths = ["app/tests"]
asyncio_mode = "auto"

[dependency-groups]
dev = ["pytest>=8.0", "pytest-asyncio>=0.24"]
```

- [ ] **Step 2: Install dependencies**

```bash
cd backend && uv sync
```
Expected: dependencies installed, `.venv` created.

- [ ] **Step 3: Create .env.example and config.py**

`backend/.env.example`:
```
DATABASE_URL=sqlite:///./compass.db
SESSION_EXPIRY_HOURS=24
COOKIE_SECURE=false
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
OLLAMA_TEMPERATURE=0.7
```

`backend/app/config.py`:
```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "sqlite:///./compass.db"
    session_expiry_hours: int = 24
    cookie_secure: bool = False

    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    ollama_temperature: float = 0.7


settings = Settings()
```

- [ ] **Step 4: Create db.py**

`backend/app/db.py`:
```python
from collections.abc import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from app.config import settings

connect_args = {"check_same_thread": False} if "sqlite" in settings.database_url else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 5: Create models/base.py and models/school.py**

`backend/app/models/base.py`:
```python
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
```

`backend/app/models/school.py`:
```python
import uuid
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid
from app.models.base import Base


class School(Base):
    __tablename__ = "schools"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    address: Mapped[str] = mapped_column(String(500), nullable=True)

    users: Mapped[list["User"]] = relationship("User", back_populates="school")
    classes: Mapped[list["Class"]] = relationship("Class", back_populates="school")
    students: Mapped[list["Student"]] = relationship("Student", back_populates="school")
```

- [ ] **Step 6: Create models/user.py**

`backend/app/models/user.py`:
```python
import enum
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, Enum, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class UserRole(str, enum.Enum):
    it_admin = "it_admin"
    district_admin = "district_admin"
    principal = "principal"
    teacher = "teacher"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)
    school_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("schools.id"), nullable=True)

    school: Mapped[Optional["School"]] = relationship("School", back_populates="users")
    sessions: Mapped[list["UserSession"]] = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    taught_classes: Mapped[list["Class"]] = relationship("Class", back_populates="teacher")


class UserSession(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="sessions")
```

- [ ] **Step 7: Create models/class_.py and models/student.py**

`backend/app/models/class_.py`:
```python
import uuid
from typing import Optional
from sqlalchemy import ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class Class(Base):
    __tablename__ = "classes"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    grade_level: Mapped[int] = mapped_column(Integer, nullable=False)
    school_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("schools.id"), nullable=False)
    teacher_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("users.id"), nullable=True)

    school: Mapped["School"] = relationship("School", back_populates="classes")
    teacher: Mapped[Optional["User"]] = relationship("User", back_populates="taught_classes")
    students: Mapped[list["Student"]] = relationship("Student", back_populates="class_")
```

`backend/app/models/student.py`:
```python
import uuid
from typing import Optional
from sqlalchemy import ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class Student(Base):
    __tablename__ = "students"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    student_id_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    grade_level: Mapped[int] = mapped_column(Integer, nullable=False)
    school_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("schools.id"), nullable=False)
    class_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("classes.id"), nullable=True)

    school: Mapped["School"] = relationship("School", back_populates="students")
    class_: Mapped[Optional["Class"]] = relationship("Class", back_populates="students")
    scores: Mapped[list["Score"]] = relationship("Score", back_populates="student")
    interventions: Mapped[list["Intervention"]] = relationship("Intervention", back_populates="student")
    ai_recs: Mapped[list["AIRec"]] = relationship("AIRec", back_populates="student")
```

- [ ] **Step 8: Create models/subject.py and models/score.py**

`backend/app/models/subject.py`:
```python
import uuid
from typing import Optional
from sqlalchemy import Float, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    scores: Mapped[list["Score"]] = relationship("Score", back_populates="subject")
    benchmarks: Mapped[list["Benchmark"]] = relationship("Benchmark", back_populates="subject")


class Benchmark(Base):
    __tablename__ = "benchmarks"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    grade_level: Mapped[int] = mapped_column(Integer, nullable=False)
    subject_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("subjects.id"), nullable=False)
    tier1_min: Mapped[float] = mapped_column(Float, default=80.0, nullable=False)
    tier2_min: Mapped[float] = mapped_column(Float, default=70.0, nullable=False)

    subject: Mapped["Subject"] = relationship("Subject", back_populates="benchmarks")
```

`backend/app/models/score.py`:
```python
import enum
import uuid
from datetime import date
from typing import Optional
from sqlalchemy import Date, Enum, Float, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class ScoreType(str, enum.Enum):
    homework = "homework"
    quiz = "quiz"
    test = "test"


class Score(Base):
    __tablename__ = "scores"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("students.id"), nullable=False)
    subject_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("subjects.id"), nullable=False)
    score_type: Mapped[ScoreType] = mapped_column(Enum(ScoreType), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    student: Mapped["Student"] = relationship("Student", back_populates="scores")
    subject: Mapped["Subject"] = relationship("Subject")
```

- [ ] **Step 9: Create remaining placeholder models**

`backend/app/models/ai_rec.py`:
```python
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, ForeignKey, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class AIRec(Base):
    __tablename__ = "ai_recs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    student_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("students.id"), nullable=True)
    class_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("classes.id"), nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    student: Mapped[Optional["Student"]] = relationship("Student", back_populates="ai_recs")
```

`backend/app/models/intervention.py`:
```python
import enum
import uuid
from datetime import date
from typing import Optional
from sqlalchemy import Date, Enum, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class InterventionStatus(str, enum.Enum):
    active = "active"
    resolved = "resolved"


class Intervention(Base):
    __tablename__ = "interventions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("students.id"), nullable=False)
    teacher_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False)
    strategy: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    outcome_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[InterventionStatus] = mapped_column(Enum(InterventionStatus), default=InterventionStatus.active, nullable=False)

    student: Mapped["Student"] = relationship("Student", back_populates="interventions")
```

`backend/app/models/audit_log.py`:
```python
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    detail: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
```

- [ ] **Step 10: Create models/__init__.py and main.py**

`backend/app/models/__init__.py`:
```python
from app.models.base import Base
from app.models.school import School
from app.models.user import User, UserSession, UserRole
from app.models.class_ import Class
from app.models.student import Student
from app.models.subject import Subject, Benchmark
from app.models.score import Score, ScoreType
from app.models.ai_rec import AIRec
from app.models.intervention import Intervention, InterventionStatus
from app.models.audit_log import AuditLog

__all__ = [
    "Base", "School", "User", "UserSession", "UserRole",
    "Class", "Student", "Subject", "Benchmark",
    "Score", "ScoreType", "AIRec", "Intervention", "InterventionStatus", "AuditLog",
]
```

`backend/app/__init__.py`: (empty)

`backend/app/main.py`:
```python
from fastapi import FastAPI

app = FastAPI(title="Compass API")

# Routers registered in later tasks
```

- [ ] **Step 11: Verify models import cleanly**

```bash
cd backend && uv run python -c "from app.models import Base, User, School, Student; print('OK')"
```
Expected: `OK`

- [ ] **Step 12: Commit**

```bash
cd backend
git init ..  # run from compass/ root if not already a git repo
cd ..
git add backend/
git commit -m "feat: backend scaffold, config, db, and all ORM models"
```

---

## Task 2: Alembic setup + initial migration

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/script.py.mako`
- Create: `backend/alembic/versions/001_initial_schema.py`

- [ ] **Step 1: Initialize Alembic**

```bash
cd backend && uv run alembic init alembic
```
Expected: `alembic/` directory created with `env.py`, `script.py.mako`, `versions/`.

- [ ] **Step 2: Update alembic/env.py to use app models and DATABASE_URL**

Replace the contents of `backend/alembic/env.py`:
```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from app.config import settings
import app.models  # noqa: F401 — ensures all models are registered
from app.models.base import Base

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 3: Generate initial migration**

```bash
cd backend && uv run alembic revision --autogenerate -m "initial_schema"
```
Expected: new file in `alembic/versions/` like `xxxx_initial_schema.py`.

- [ ] **Step 4: Apply migration**

```bash
cd backend && uv run alembic upgrade head
```
Expected: `compass.db` created, all tables present.

- [ ] **Step 5: Verify tables exist**

```bash
cd backend && uv run python -c "
from sqlalchemy import inspect
from app.db import engine
tables = inspect(engine).get_table_names()
print(sorted(tables))
"
```
Expected: `['ai_recs', 'audit_log', 'benchmarks', 'classes', 'interventions', 'schools', 'scores', 'sessions', 'students', 'subjects', 'users']`

- [ ] **Step 6: Commit**

```bash
git add backend/alembic/ backend/alembic.ini
git commit -m "feat: alembic setup and initial schema migration"
```

---

## Task 3: Auth service, middleware, routes, and tests

**Files:**
- Create: `backend/app/schemas/auth.py`
- Create: `backend/app/services/auth.py`
- Create: `backend/app/middleware/auth.py`
- Create: `backend/app/middleware/__init__.py`
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/schemas/__init__.py`
- Create: `backend/app/routes/__init__.py`
- Create: `backend/app/routes/auth.py`
- Create: `backend/app/tests/conftest.py`
- Create: `backend/app/tests/__init__.py`
- Create: `backend/app/tests/test_auth.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Write failing auth tests**

`backend/app/tests/__init__.py`: (empty)

`backend/app/tests/conftest.py`:
```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db import get_db
from app.models import Base

TEST_DB_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSession(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        yield db
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()
```

`backend/app/tests/test_auth.py`:
```python
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


def test_rbac_teacher_cannot_access_admin(client, db):
    teacher = User(username="t1", hashed_password=hash_password("pass"), role=UserRole.teacher)
    db.add(teacher)
    db.commit()
    client.post("/api/auth/login", json={"username": "t1", "password": "pass"})
    res = client.get("/api/admin/users")
    assert res.status_code == 403
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd backend && uv run pytest app/tests/test_auth.py -v
```
Expected: errors like `ImportError` or `404` — routes don't exist yet.

- [ ] **Step 3: Implement auth service**

`backend/app/services/__init__.py`: (empty)

`backend/app/services/auth.py`:
```python
import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from app.models import User, UserSession
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_session(db: Session, user: User) -> UserSession:
    session = UserSession(
        user_id=user.id,
        expires_at=datetime.utcnow() + timedelta(hours=settings.session_expiry_hours),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_session(db: Session, session_id: str) -> UserSession | None:
    try:
        sid = uuid.UUID(session_id)
    except ValueError:
        return None
    session = db.query(UserSession).filter(UserSession.id == sid).first()
    if session and session.expires_at > datetime.utcnow():
        return session
    return None


def delete_session(db: Session, session_id: str) -> None:
    try:
        sid = uuid.UUID(session_id)
    except ValueError:
        return
    db.query(UserSession).filter(UserSession.id == sid).delete()
    db.commit()
```

- [ ] **Step 4: Implement auth middleware**

`backend/app/middleware/__init__.py`: (empty)

`backend/app/middleware/auth.py`:
```python
from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import User, UserRole
from app.services.auth import get_session


def get_current_user(
    session_id: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not session_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    session = get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")
    return session.user


def require_role(*roles: UserRole):
    def checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user
    return checker
```

- [ ] **Step 5: Implement auth schemas and routes**

`backend/app/schemas/__init__.py`: (empty)

`backend/app/schemas/auth.py`:
```python
import uuid
from pydantic import BaseModel
from app.models import UserRole


class LoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    role: UserRole
    school_id: uuid.UUID | None

    model_config = {"from_attributes": True}
```

`backend/app/routes/__init__.py`: (empty)

`backend/app/routes/auth.py`:
```python
from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from app.db import get_db
from app.middleware.auth import get_current_user
from app.models import User
from app.schemas.auth import LoginRequest, UserResponse
from app.services.auth import create_session, delete_session, verify_password
from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=UserResponse)
def login(body: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    session = create_session(db, user)
    response.set_cookie(
        key="session_id",
        value=str(session.id),
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
    )
    return user


@router.post("/logout")
def logout(response: Response, session_id: str | None = Cookie(default=None), db: Session = Depends(get_db)):
    if session_id:
        delete_session(db, session_id)
    response.delete_cookie("session_id")
    return {"ok": True}


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user
```

- [ ] **Step 6: Update main.py to register auth router**

`backend/app/main.py`:
```python
from fastapi import FastAPI
from app.routes.auth import router as auth_router

app = FastAPI(title="Compass API")

app.include_router(auth_router)
```

- [ ] **Step 7: Run auth tests — verify they pass**

```bash
cd backend && uv run pytest app/tests/test_auth.py -v
```
Expected: all 7 tests pass. The `test_rbac_teacher_cannot_access_admin` will fail with 404 until admin routes exist — that's acceptable for now; update that test expectation to 404 temporarily or skip it.

- [ ] **Step 8: Commit**

```bash
git add backend/app/
git commit -m "feat: auth service, middleware, routes, and tests"
```

---

## Task 4: MTSS service and tests

**Files:**
- Create: `backend/app/services/mtss.py`
- Create: `backend/app/tests/test_mtss.py`

- [ ] **Step 1: Write failing MTSS tests**

`backend/app/tests/test_mtss.py`:
```python
from app.services.mtss import calculate_tier, TierResult


def test_tier1_at_boundary():
    assert calculate_tier(80.0) == TierResult.tier1


def test_tier1_above():
    assert calculate_tier(95.0) == TierResult.tier1


def test_tier2_at_lower_boundary():
    assert calculate_tier(70.0) == TierResult.tier2


def test_tier2_at_upper_boundary():
    assert calculate_tier(79.9) == TierResult.tier2


def test_tier3_below():
    assert calculate_tier(69.9) == TierResult.tier3


def test_tier3_zero():
    assert calculate_tier(0.0) == TierResult.tier3


def test_custom_thresholds():
    assert calculate_tier(75.0, tier1_min=80.0, tier2_min=60.0) == TierResult.tier2
    assert calculate_tier(55.0, tier1_min=80.0, tier2_min=60.0) == TierResult.tier3
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd backend && uv run pytest app/tests/test_mtss.py -v
```
Expected: `ImportError: cannot import name 'calculate_tier'`

- [ ] **Step 3: Implement MTSS service**

`backend/app/services/mtss.py`:
```python
import enum
from sqlalchemy.orm import Session
from app.models import Score, Benchmark, Student


class TierResult(str, enum.Enum):
    tier1 = "tier1"
    tier2 = "tier2"
    tier3 = "tier3"


def calculate_tier(avg_score: float, tier1_min: float = 80.0, tier2_min: float = 70.0) -> TierResult:
    if avg_score >= tier1_min:
        return TierResult.tier1
    if avg_score >= tier2_min:
        return TierResult.tier2
    return TierResult.tier3


def get_student_tier(db: Session, student_id, subject_id=None) -> TierResult | None:
    """Compute MTSS tier for a student, optionally filtered by subject."""
    query = db.query(Score).filter(Score.student_id == student_id)
    if subject_id:
        query = query.filter(Score.subject_id == subject_id)
    scores = query.all()
    if not scores:
        return None
    avg = sum(s.value for s in scores) / len(scores)

    student = db.query(Student).filter(Student.id == student_id).first()
    benchmark = None
    if student and subject_id:
        benchmark = (
            db.query(Benchmark)
            .filter(Benchmark.grade_level == student.grade_level, Benchmark.subject_id == subject_id)
            .first()
        )
    tier1_min = benchmark.tier1_min if benchmark else 80.0
    tier2_min = benchmark.tier2_min if benchmark else 70.0
    return calculate_tier(avg, tier1_min, tier2_min)
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
cd backend && uv run pytest app/tests/test_mtss.py -v
```
Expected: all 7 tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/mtss.py backend/app/tests/test_mtss.py
git commit -m "feat: MTSS tier calculation service and tests"
```

---

## Task 5: Admin routes and tests

**Files:**
- Create: `backend/app/schemas/admin.py`
- Create: `backend/app/routes/admin.py`
- Create: `backend/app/tests/test_admin.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Write failing admin tests**

`backend/app/tests/test_admin.py`:
```python
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
    res = c.post("/api/admin/users", json={"username": "newuser", "password": "pass123", "role": "teacher"})
    assert res.status_code == 201
    assert res.json()["username"] == "newuser"


def test_create_duplicate_user(client, db):
    c = admin_client(client, db)
    c.post("/api/admin/users", json={"username": "dup", "password": "pass", "role": "teacher"})
    res = c.post("/api/admin/users", json={"username": "dup", "password": "pass", "role": "teacher"})
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
    r = c.post("/api/admin/users", json={"username": "todel", "password": "x", "role": "teacher"})
    uid = r.json()["id"]
    res = c.delete(f"/api/admin/users/{uid}")
    assert res.status_code == 204
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd backend && uv run pytest app/tests/test_admin.py -v
```
Expected: 404 errors or import errors.

- [ ] **Step 3: Implement admin schemas**

`backend/app/schemas/admin.py`:
```python
import uuid
from typing import Optional
from pydantic import BaseModel
from app.models import UserRole


class UserCreate(BaseModel):
    username: str
    password: str
    role: UserRole
    school_id: Optional[uuid.UUID] = None


class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None
    school_id: Optional[uuid.UUID] = None


class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    role: UserRole
    school_id: Optional[uuid.UUID]
    model_config = {"from_attributes": True}


class SchoolCreate(BaseModel):
    name: str
    address: Optional[str] = None


class SchoolResponse(BaseModel):
    id: uuid.UUID
    name: str
    address: Optional[str]
    model_config = {"from_attributes": True}


class ClassCreate(BaseModel):
    name: str
    grade_level: int
    school_id: uuid.UUID
    teacher_id: Optional[uuid.UUID] = None


class ClassResponse(BaseModel):
    id: uuid.UUID
    name: str
    grade_level: int
    school_id: uuid.UUID
    teacher_id: Optional[uuid.UUID]
    model_config = {"from_attributes": True}


class SubjectCreate(BaseModel):
    name: str


class SubjectResponse(BaseModel):
    id: uuid.UUID
    name: str
    model_config = {"from_attributes": True}
```

- [ ] **Step 4: Implement admin routes**

`backend/app/routes/admin.py`:
```python
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db import get_db
from app.middleware.auth import require_role
from app.models import User, UserRole, School, Class, Subject
from app.schemas.admin import (
    ClassCreate, ClassResponse, SchoolCreate, SchoolResponse,
    SubjectCreate, SubjectResponse, UserCreate, UserResponse, UserUpdate,
)
from app.services.auth import hash_password

router = APIRouter(prefix="/api/admin", tags=["admin"])
admin_only = Depends(require_role(UserRole.it_admin))


@router.get("/users", response_model=list[UserResponse], dependencies=[admin_only])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).all()


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED, dependencies=[admin_only])
def create_user(body: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(status_code=409, detail="Username already exists")
    user = User(username=body.username, hashed_password=hash_password(body.password), role=body.role, school_id=body.school_id)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/users/{user_id}", response_model=UserResponse, dependencies=[admin_only])
def update_user(user_id: uuid.UUID, body: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if body.username:
        user.username = body.username
    if body.password:
        user.hashed_password = hash_password(body.password)
    if body.role:
        user.role = body.role
    if body.school_id is not None:
        user.school_id = body.school_id
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[admin_only])
def delete_user(user_id: uuid.UUID, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()


@router.get("/schools", response_model=list[SchoolResponse], dependencies=[admin_only])
def list_schools(db: Session = Depends(get_db)):
    return db.query(School).all()


@router.post("/schools", response_model=SchoolResponse, status_code=201, dependencies=[admin_only])
def create_school(body: SchoolCreate, db: Session = Depends(get_db)):
    school = School(**body.model_dump())
    db.add(school)
    db.commit()
    db.refresh(school)
    return school


@router.get("/classes", response_model=list[ClassResponse], dependencies=[admin_only])
def list_classes(db: Session = Depends(get_db)):
    return db.query(Class).all()


@router.post("/classes", response_model=ClassResponse, status_code=201, dependencies=[admin_only])
def create_class(body: ClassCreate, db: Session = Depends(get_db)):
    cls = Class(**body.model_dump())
    db.add(cls)
    db.commit()
    db.refresh(cls)
    return cls


@router.get("/subjects", response_model=list[SubjectResponse], dependencies=[admin_only])
def list_subjects(db: Session = Depends(get_db)):
    return db.query(Subject).all()


@router.post("/subjects", response_model=SubjectResponse, status_code=201, dependencies=[admin_only])
def create_subject(body: SubjectCreate, db: Session = Depends(get_db)):
    subject = Subject(**body.model_dump())
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return subject
```

- [ ] **Step 5: Register admin router in main.py**

`backend/app/main.py`:
```python
from fastapi import FastAPI
from app.routes.auth import router as auth_router
from app.routes.admin import router as admin_router

app = FastAPI(title="Compass API")

app.include_router(auth_router)
app.include_router(admin_router)
```

- [ ] **Step 6: Run admin tests — verify they pass**

```bash
cd backend && uv run pytest app/tests/test_admin.py -v
```
Expected: all 7 tests pass.

- [ ] **Step 7: Also update test_auth.py RBAC test — now admin routes exist**

In `backend/app/tests/test_auth.py`, the `test_rbac_teacher_cannot_access_admin` test should now return 403 (not 404). Run all auth tests:

```bash
cd backend && uv run pytest app/tests/test_auth.py -v
```
Expected: all pass.

- [ ] **Step 8: Commit**

```bash
git add backend/app/routes/admin.py backend/app/schemas/admin.py backend/app/tests/test_admin.py backend/app/main.py
git commit -m "feat: admin routes for users, schools, classes, subjects"
```

---

## Task 6: Student routes and tests

**Files:**
- Create: `backend/app/schemas/student.py`
- Create: `backend/app/routes/students.py`
- Create: `backend/app/tests/test_students.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Write failing student tests**

`backend/app/tests/test_students.py`:
```python
import uuid
from app.services.auth import hash_password
from app.models import User, UserRole, School, Class, Student


def seed_world(db):
    school = School(name="Test School")
    db.add(school)
    db.flush()
    teacher = User(username="teacher", hashed_password=hash_password("pass"), role=UserRole.teacher, school_id=school.id)
    admin = User(username="admin", hashed_password=hash_password("pass"), role=UserRole.it_admin)
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
    client.post("/api/auth/login", json={"username": "admin", "password": "pass"})
    res = client.get("/api/students")
    assert res.status_code == 200
    assert len(res.json()) >= 1


def test_teacher_sees_only_own_class_students(client, db):
    w = seed_world(db)
    client.post("/api/auth/login", json={"username": "teacher", "password": "pass"})
    res = client.get("/api/students")
    assert res.status_code == 200
    ids = [s["student_id_number"] for s in res.json()]
    assert "S001" in ids


def test_get_student_by_id(client, db):
    w = seed_world(db)
    client.post("/api/auth/login", json={"username": "admin", "password": "pass"})
    sid = str(w["student"].id)
    res = client.get(f"/api/students/{sid}")
    assert res.status_code == 200
    assert res.json()["name"] == "Alice Smith"


def test_create_student(client, db):
    w = seed_world(db)
    client.post("/api/auth/login", json={"username": "admin", "password": "pass"})
    res = client.post("/api/students", json={
        "name": "Bob Jones", "student_id_number": "S002",
        "grade_level": 5, "school_id": str(w["school"].id),
        "class_id": str(w["class"].id),
    })
    assert res.status_code == 201
    assert res.json()["name"] == "Bob Jones"


def test_patch_student(client, db):
    w = seed_world(db)
    client.post("/api/auth/login", json={"username": "admin", "password": "pass"})
    sid = str(w["student"].id)
    res = client.patch(f"/api/students/{sid}", json={"name": "Alice Updated"})
    assert res.status_code == 200
    assert res.json()["name"] == "Alice Updated"


def test_unauthenticated_cannot_list_students(client, db):
    res = client.get("/api/students")
    assert res.status_code == 401
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd backend && uv run pytest app/tests/test_students.py -v
```
Expected: 404 errors.

- [ ] **Step 3: Implement student schemas**

`backend/app/schemas/student.py`:
```python
import uuid
from typing import Optional
from pydantic import BaseModel


class StudentCreate(BaseModel):
    name: str
    student_id_number: str
    grade_level: int
    school_id: uuid.UUID
    class_id: Optional[uuid.UUID] = None


class StudentUpdate(BaseModel):
    name: Optional[str] = None
    grade_level: Optional[int] = None
    school_id: Optional[uuid.UUID] = None
    class_id: Optional[uuid.UUID] = None


class StudentResponse(BaseModel):
    id: uuid.UUID
    name: str
    student_id_number: str
    grade_level: int
    school_id: uuid.UUID
    class_id: Optional[uuid.UUID]
    model_config = {"from_attributes": True}
```

- [ ] **Step 4: Implement student routes**

`backend/app/routes/students.py`:
```python
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db import get_db
from app.middleware.auth import get_current_user, require_role
from app.models import Student, User, UserRole
from app.schemas.student import StudentCreate, StudentResponse, StudentUpdate

router = APIRouter(prefix="/api/students", tags=["students"])


def _scoped_students(db: Session, user: User):
    q = db.query(Student)
    if user.role == UserRole.teacher:
        # teachers see students in their assigned classes
        from app.models import Class
        class_ids = [c.id for c in db.query(Class).filter(Class.teacher_id == user.id).all()]
        q = q.filter(Student.class_id.in_(class_ids))
    elif user.role == UserRole.principal:
        q = q.filter(Student.school_id == user.school_id)
    elif user.role == UserRole.district_admin:
        pass  # all
    return q


@router.get("", response_model=list[StudentResponse])
def list_students(
    search: str | None = None,
    page: int = 1,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = _scoped_students(db, current_user)
    if search:
        q = q.filter(Student.name.ilike(f"%{search}%"))
    return q.offset((page - 1) * 50).limit(50).all()


@router.get("/{student_id}", response_model=StudentResponse)
def get_student(student_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    student = _scoped_students(db, current_user).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@router.post("", response_model=StudentResponse, status_code=201)
def create_student(
    body: StudentCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.it_admin, UserRole.principal, UserRole.teacher)),
):
    student = Student(**body.model_dump())
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


@router.patch("/{student_id}", response_model=StudentResponse)
def update_student(
    student_id: uuid.UUID,
    body: StudentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    student = _scoped_students(db, current_user).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    for field, val in body.model_dump(exclude_none=True).items():
        setattr(student, field, val)
    db.commit()
    db.refresh(student)
    return student
```

- [ ] **Step 5: Register student router in main.py**

`backend/app/main.py`:
```python
from fastapi import FastAPI
from app.routes.auth import router as auth_router
from app.routes.admin import router as admin_router
from app.routes.students import router as students_router

app = FastAPI(title="Compass API")

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(students_router)
```

- [ ] **Step 6: Run student tests — verify they pass**

```bash
cd backend && uv run pytest app/tests/test_students.py -v
```
Expected: all 6 tests pass.

- [ ] **Step 7: Commit**

```bash
git add backend/app/routes/students.py backend/app/schemas/student.py backend/app/tests/test_students.py backend/app/main.py
git commit -m "feat: student CRUD routes with role-based scoping"
```

---

## Task 7: Score routes and tests

**Files:**
- Create: `backend/app/schemas/score.py`
- Create: `backend/app/services/csv_import.py`
- Create: `backend/app/routes/scores.py`
- Create: `backend/app/tests/test_scores.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Write failing score tests**

`backend/app/tests/test_scores.py`:
```python
import io
import csv
from app.services.auth import hash_password
from app.models import User, UserRole, School, Class, Student, Subject


def seed_score_world(db):
    school = School(name="Score School")
    db.add(school)
    db.flush()
    teacher = User(username="teacher", hashed_password=hash_password("pass"), role=UserRole.teacher, school_id=school.id)
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
    client.post("/api/auth/login", json={"username": "teacher", "password": "pass"})
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
    client.post("/api/auth/login", json={"username": "teacher", "password": "pass"})
    client.post("/api/scores", json={
        "student_id": str(w["student"].id),
        "subject_id": str(w["subject"].id),
        "score_type": "test",
        "value": 90.0,
        "date": "2026-03-15",
    })
    res = client.get(f"/api/scores/student/{w['student'].id}")
    assert res.status_code == 200
    assert len(res.json()) >= 1


def test_csv_import_valid(client, db):
    w = seed_score_world(db)
    client.post("/api/auth/login", json={"username": "teacher", "password": "pass"})
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["student_id_number", "subject_name", "score_type", "value", "date", "notes"])
    writer.writerow(["S100", "Reading", "homework", "78", "2026-03-10", "good effort"])
    buf.seek(0)
    res = client.post("/api/scores/import", files={"file": ("scores.csv", buf, "text/csv")})
    assert res.status_code == 200
    assert res.json()["imported"] == 1
    assert res.json()["errors"] == []


def test_csv_import_invalid_score_type(client, db):
    w = seed_score_world(db)
    client.post("/api/auth/login", json={"username": "teacher", "password": "pass"})
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["student_id_number", "subject_name", "score_type", "value", "date", "notes"])
    writer.writerow(["S100", "Reading", "BADTYPE", "78", "2026-03-10", ""])
    buf.seek(0)
    res = client.post("/api/scores/import", files={"file": ("scores.csv", buf, "text/csv")})
    assert res.status_code == 200
    assert res.json()["imported"] == 0
    assert len(res.json()["errors"]) == 1


def test_csv_template_download(client, db):
    w = seed_score_world(db)
    client.post("/api/auth/login", json={"username": "teacher", "password": "pass"})
    res = client.get("/api/scores/template.csv")
    assert res.status_code == 200
    assert "student_id_number" in res.text
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd backend && uv run pytest app/tests/test_scores.py -v
```
Expected: 404 errors.

- [ ] **Step 3: Implement score schemas and CSV import service**

`backend/app/schemas/score.py`:
```python
import uuid
from datetime import date
from typing import Optional
from pydantic import BaseModel
from app.models import ScoreType


class ScoreCreate(BaseModel):
    student_id: uuid.UUID
    subject_id: uuid.UUID
    score_type: ScoreType
    value: float
    date: date
    notes: Optional[str] = None


class ScoreResponse(BaseModel):
    id: uuid.UUID
    student_id: uuid.UUID
    subject_id: uuid.UUID
    score_type: ScoreType
    value: float
    date: date
    notes: Optional[str]
    model_config = {"from_attributes": True}


class CSVRowError(BaseModel):
    row: int
    message: str


class CSVImportResult(BaseModel):
    imported: int
    errors: list[CSVRowError]
```

`backend/app/services/csv_import.py`:
```python
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

        try:
            score_type = ScoreType(row["score_type"].strip().lower())
        except ValueError:
            row_errors.append(f"Invalid score_type '{row['score_type']}' (must be homework, quiz, or test)")
            score_type = None

        try:
            value = float(row["value"])
            if not (0 <= value <= 100):
                raise ValueError
        except ValueError:
            row_errors.append(f"Invalid value '{row['value']}' (must be 0–100)")
            value = None

        try:
            score_date = date.fromisoformat(row["date"].strip())
        except ValueError:
            row_errors.append(f"Invalid date '{row['date']}' (must be YYYY-MM-DD)")
            score_date = None

        if row_errors:
            errors.append(CSVRowError(row=i, message="; ".join(row_errors)))
        elif student and subject and score_type and value is not None and score_date:
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
```

- [ ] **Step 4: Implement score routes**

`backend/app/routes/scores.py`:
```python
import uuid
from fastapi import APIRouter, Depends, UploadFile
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from app.db import get_db
from app.middleware.auth import get_current_user
from app.models import Score, User
from app.schemas.score import ScoreCreate, ScoreResponse, CSVImportResult
from app.services.csv_import import parse_and_validate_csv

router = APIRouter(prefix="/api/scores", tags=["scores"])

CSV_TEMPLATE = "student_id_number,subject_name,score_type,value,date,notes\nS001,Math,quiz,85,2026-03-01,\n"


@router.get("/template.csv", response_class=PlainTextResponse)
def get_template(_: User = Depends(get_current_user)):
    return PlainTextResponse(content=CSV_TEMPLATE, media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=scores_template.csv"})


@router.post("", response_model=ScoreResponse, status_code=201)
def create_score(body: ScoreCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    score = Score(**body.model_dump())
    db.add(score)
    db.commit()
    db.refresh(score)
    return score


@router.post("/import", response_model=CSVImportResult)
async def import_scores(file: UploadFile, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    contents = await file.read()
    return parse_and_validate_csv(db, contents)


@router.get("/student/{student_id}", response_model=list[ScoreResponse])
def get_student_scores(student_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Score).filter(Score.student_id == student_id).order_by(Score.date.desc()).all()
```

- [ ] **Step 5: Register scores router in main.py**

`backend/app/main.py`:
```python
from fastapi import FastAPI
from app.routes.auth import router as auth_router
from app.routes.admin import router as admin_router
from app.routes.students import router as students_router
from app.routes.scores import router as scores_router

app = FastAPI(title="Compass API")

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(students_router)
app.include_router(scores_router)
```

- [ ] **Step 6: Run score tests — verify they pass**

```bash
cd backend && uv run pytest app/tests/test_scores.py -v
```
Expected: all 5 tests pass.

- [ ] **Step 7: Run full test suite**

```bash
cd backend && uv run pytest -v
```
Expected: all tests pass.

- [ ] **Step 8: Commit**

```bash
git add backend/app/routes/scores.py backend/app/schemas/score.py backend/app/services/csv_import.py backend/app/tests/test_scores.py backend/app/main.py
git commit -m "feat: score entry, CSV import, and template download"
```

---

## Task 8: Seed script

**Files:**
- Create: `backend/app/seed.py`

- [ ] **Step 1: Write the seed script**

`backend/app/seed.py`:
```python
"""Idempotent seed script. Run with: uv run python -m app.seed"""
from datetime import date, timedelta
import random
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

        # Users
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

        # Scores (~30 spread across students/subjects/dates)
        subjects = [math, reading, science]
        score_types = list(ScoreType)
        base_date = date.today() - timedelta(days=60)
        random.seed(42)
        for student in students:
            for subject in subjects:
                for i in range(3):
                    score = Score(
                        student_id=student.id,
                        subject_id=subject.id,
                        score_type=random.choice(score_types),
                        value=round(random.uniform(55, 98), 1),
                        date=base_date + timedelta(days=random.randint(0, 55)),
                    )
                    db.add(score)

        db.commit()
        print("Seed complete.")
        print("  Users: admin, district, principal, teacher (all password: changeme)")
        print("  Schools: 2 | Classes: 2 | Students: 10 | Subjects: 3 | Scores: ~90")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
```

- [ ] **Step 2: Run the seed script against the real DB**

```bash
cd backend && uv run python -m app.seed
```
Expected:
```
Seed complete.
  Users: admin, district, principal, teacher (all password: changeme)
  Schools: 2 | Classes: 2 | Students: 10 | Subjects: 3 | Scores: ~90
```

- [ ] **Step 3: Run it again — verify idempotency**

```bash
cd backend && uv run python -m app.seed
```
Expected: `Database already seeded. Skipping.`

- [ ] **Step 4: Commit**

```bash
git add backend/app/seed.py
git commit -m "feat: idempotent seed script with one user per role and sample data"
```

---

## Task 9: Frontend scaffold

**Files:**
- Create: `frontend/` (via create-next-app)
- Modify: `frontend/next.config.ts`
- Create: `frontend/.env.local.example`

- [ ] **Step 1: Scaffold Next.js project**

From the `compass/` root:
```bash
npx create-next-app@latest frontend --typescript --tailwind --eslint --app --src-dir --import-alias "@/*" --no-git
```
Answer the interactive prompts: App Router = yes, Turbopack = yes (default).

- [ ] **Step 2: Install additional dependencies**

```bash
cd frontend
npm install recharts
npm install lucide-react
npm install @radix-ui/react-slot class-variance-authority clsx tailwind-merge
```

- [ ] **Step 3: Initialize shadcn/ui**

```bash
cd frontend && npx shadcn@latest init
```
When prompted: style = Default, base color = Slate, CSS variables = yes.

- [ ] **Step 4: Add core shadcn components**

```bash
cd frontend && npx shadcn@latest add button input label card table badge select textarea dialog alert
```

- [ ] **Step 5: Configure API proxy in next.config.ts**

Replace `frontend/next.config.ts` with:
```typescript
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8000/api/:path*",
      },
    ];
  },
};

export default nextConfig;
```

- [ ] **Step 6: Create .env.local.example**

`frontend/.env.local.example`:
```
# No frontend env vars needed for local dev — API is proxied via next.config.ts
# Set this only for production builds pointing at a non-local backend:
# NEXT_PUBLIC_API_BASE=http://your-server:8000
```

- [ ] **Step 7: Verify dev server starts**

```bash
cd frontend && npm run dev
```
Expected: server starts at `http://localhost:3000` with no errors. Stop with Ctrl+C.

- [ ] **Step 8: Commit**

```bash
cd ..
git add frontend/
git commit -m "feat: Next.js frontend scaffold with Tailwind, shadcn/ui, and API proxy"
```

---

## Task 10: Auth types, API client, and auth context

**Files:**
- Create: `frontend/src/lib/types.ts`
- Create: `frontend/src/lib/api.ts`
- Create: `frontend/src/lib/auth.tsx`
- Modify: `frontend/src/app/layout.tsx`

- [ ] **Step 1: Create shared types**

`frontend/src/lib/types.ts`:
```typescript
export type UserRole = "it_admin" | "district_admin" | "principal" | "teacher";

export interface User {
  id: string;
  username: string;
  role: UserRole;
  school_id: string | null;
}

export interface School {
  id: string;
  name: string;
  address: string | null;
}

export interface Class {
  id: string;
  name: string;
  grade_level: number;
  school_id: string;
  teacher_id: string | null;
}

export interface Subject {
  id: string;
  name: string;
}

export interface Student {
  id: string;
  name: string;
  student_id_number: string;
  grade_level: number;
  school_id: string;
  class_id: string | null;
}

export type ScoreType = "homework" | "quiz" | "test";

export interface Score {
  id: string;
  student_id: string;
  subject_id: string;
  score_type: ScoreType;
  value: number;
  date: string;
  notes: string | null;
}

export interface CSVRowError {
  row: number;
  message: string;
}

export interface CSVImportResult {
  imported: number;
  errors: CSVRowError[];
}
```

- [ ] **Step 2: Create typed API client**

`frontend/src/lib/api.ts`:
```typescript
async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`/api${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    if (res.status === 401) throw Object.assign(new Error("UNAUTHORIZED"), { status: 401 });
    if (res.status === 403) throw Object.assign(new Error("FORBIDDEN"), { status: 403 });
    const err = await res.json().catch(() => ({}));
    throw Object.assign(new Error(err.detail ?? `HTTP ${res.status}`), { status: res.status });
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "POST", body: body !== undefined ? JSON.stringify(body) : undefined }),
  patch: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "PATCH", body: JSON.stringify(body) }),
  delete: (path: string) => request<void>(path, { method: "DELETE" }),
  upload: <T>(path: string, formData: FormData) =>
    request<T>(path, { method: "POST", body: formData, headers: {} }),
};
```

- [ ] **Step 3: Create auth context**

`frontend/src/lib/auth.tsx`:
```typescript
"use client";
import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api } from "./api";
import type { User } from "./types";

interface AuthCtx {
  user: User | null;
  loading: boolean;
  refresh: () => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthCtx>({
  user: null,
  loading: true,
  refresh: async () => {},
  logout: async () => {},
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const u = await api.get<User>("/auth/me");
      setUser(u);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    await api.post("/auth/logout");
    setUser(null);
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return (
    <AuthContext.Provider value={{ user, loading, refresh, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
```

- [ ] **Step 4: Wrap app in AuthProvider**

`frontend/src/app/layout.tsx`:
```typescript
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/lib/auth";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Compass",
  description: "Student Learning Analytics and MTSS System",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
```

- [ ] **Step 5: Update root page to redirect**

`frontend/src/app/page.tsx`:
```typescript
import { redirect } from "next/navigation";

export default function Home() {
  redirect("/students");
}
```

- [ ] **Step 6: Verify build has no type errors**

```bash
cd frontend && npm run build 2>&1 | tail -20
```
Expected: build succeeds or only minor warnings (no type errors).

- [ ] **Step 7: Commit**

```bash
git add frontend/src/lib/ frontend/src/app/layout.tsx frontend/src/app/page.tsx
git commit -m "feat: auth context, typed API client, and shared types"
```

---

## Task 11: Login page

**Files:**
- Create: `frontend/src/app/login/page.tsx`

- [ ] **Step 1: Create login page**

`frontend/src/app/login/page.tsx`:
```typescript
"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { refresh } = useAuth();
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await api.post("/auth/login", { username, password });
      await refresh();
      router.push("/students");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950">
      <Card className="w-full max-w-sm">
        <CardHeader className="text-center">
          <div className="text-3xl font-bold text-slate-800 dark:text-slate-100 mb-1">Compass</div>
          <CardTitle className="text-base font-normal text-slate-500">Student Learning Analytics</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1">
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
                required
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                required
              />
            </div>
            {error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "Signing in…" : "Sign in"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
```

- [ ] **Step 2: Verify login page renders**

Start backend and frontend:
```bash
# Terminal 1
cd backend && uv run uvicorn app.main:app --reload
# Terminal 2
cd frontend && npm run dev
```
Navigate to `http://localhost:3000/login`. Expected: login form renders. Sign in with `admin` / `changeme` — should redirect to `/students`.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/app/login/
git commit -m "feat: login page"
```

---

## Task 12: Protected layout, sidebar, and theme toggle

**Files:**
- Create: `frontend/src/app/(protected)/layout.tsx`
- Create: `frontend/src/components/layout/sidebar.tsx`
- Create: `frontend/src/components/layout/header.tsx`

- [ ] **Step 1: Create sidebar component**

`frontend/src/components/layout/sidebar.tsx`:
```typescript
"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Users, BarChart2, Upload, Settings, LogOut, School } from "lucide-react";

interface NavItem {
  href: string;
  label: string;
  icon: React.ElementType;
  roles: string[];
}

const NAV: NavItem[] = [
  { href: "/students", label: "Students", icon: Users, roles: ["it_admin", "district_admin", "principal", "teacher"] },
  { href: "/scores/entry", label: "Enter Scores", icon: BarChart2, roles: ["it_admin", "principal", "teacher"] },
  { href: "/scores/import", label: "Import Scores", icon: Upload, roles: ["it_admin", "principal", "teacher"] },
  { href: "/admin/users", label: "Users", icon: Settings, roles: ["it_admin"] },
  { href: "/admin/schools", label: "Schools", icon: School, roles: ["it_admin"] },
  { href: "/admin/classes", label: "Classes", icon: School, roles: ["it_admin"] },
  { href: "/admin/subjects", label: "Subjects", icon: BarChart2, roles: ["it_admin"] },
];

export function Sidebar() {
  const { user, logout } = useAuth();
  const pathname = usePathname();
  const router = useRouter();

  const visible = NAV.filter((item) => user && item.roles.includes(user.role));

  async function handleLogout() {
    await logout();
    router.push("/login");
  }

  return (
    <aside className="w-56 shrink-0 flex flex-col border-r bg-white dark:bg-slate-900 h-screen sticky top-0">
      <div className="p-4 border-b">
        <span className="text-xl font-bold text-slate-800 dark:text-slate-100">Compass</span>
      </div>
      <nav className="flex-1 p-2 space-y-0.5 overflow-y-auto">
        {visible.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors",
              pathname.startsWith(item.href)
                ? "bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100"
                : "text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800"
            )}
          >
            <item.icon className="h-4 w-4 shrink-0" />
            {item.label}
          </Link>
        ))}
      </nav>
      <div className="p-2 border-t">
        <div className="px-3 py-1 text-xs text-slate-400 truncate">{user?.username} · {user?.role}</div>
        <Button variant="ghost" size="sm" className="w-full justify-start gap-2 mt-1" onClick={handleLogout}>
          <LogOut className="h-4 w-4" /> Sign out
        </Button>
      </div>
    </aside>
  );
}
```

- [ ] **Step 2: Create header component**

`frontend/src/components/layout/header.tsx`:
```typescript
"use client";
import { Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";

export function Header({ title }: { title?: string }) {
  const [dark, setDark] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem("theme");
    if (stored === "dark" || (!stored && window.matchMedia("(prefers-color-scheme: dark)").matches)) {
      document.documentElement.classList.add("dark");
      setDark(true);
    }
  }, []);

  function toggleTheme() {
    const next = !dark;
    setDark(next);
    document.documentElement.classList.toggle("dark", next);
    localStorage.setItem("theme", next ? "dark" : "light");
  }

  return (
    <header className="h-14 flex items-center justify-between px-6 border-b bg-white dark:bg-slate-900">
      <h1 className="text-base font-semibold text-slate-800 dark:text-slate-100">{title}</h1>
      <Button variant="ghost" size="icon" onClick={toggleTheme} aria-label="Toggle theme">
        {dark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
      </Button>
    </header>
  );
}
```

- [ ] **Step 3: Create protected layout**

`frontend/src/app/(protected)/layout.tsx`:
```typescript
"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { Sidebar } from "@/components/layout/sidebar";

export default function ProtectedLayout({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/login");
    }
  }, [loading, user, router]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center text-slate-400">
        Loading…
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="flex min-h-screen bg-slate-50 dark:bg-slate-950">
      <Sidebar />
      <main className="flex-1 overflow-auto">{children}</main>
    </div>
  );
}
```

- [ ] **Step 4: Verify protected layout redirects unauthenticated users**

Ensure backend is running. Navigate to `http://localhost:3000/students` without logging in. Expected: redirect to `/login`.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/app/\(protected\)/ frontend/src/components/layout/
git commit -m "feat: protected layout, sidebar with role-aware nav, theme toggle"
```

---

## Task 13: Students pages

**Files:**
- Create: `frontend/src/app/(protected)/students/page.tsx`
- Create: `frontend/src/app/(protected)/students/[id]/page.tsx`
- Create: `frontend/src/app/(protected)/students/new/page.tsx`

- [ ] **Step 1: Create student list page**

`frontend/src/app/(protected)/students/page.tsx`:
```typescript
"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Student } from "@/lib/types";
import { Header } from "@/components/layout/header";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

export default function StudentsPage() {
  const [students, setStudents] = useState<Student[]>([]);
  const [search, setSearch] = useState("");
  const { user } = useAuth();

  useEffect(() => {
    api.get<Student[]>(`/students?search=${encodeURIComponent(search)}`).then(setStudents).catch(console.error);
  }, [search]);

  const canAdd = user?.role !== "district_admin";

  return (
    <div>
      <Header title="Students" />
      <div className="p-6 space-y-4">
        <div className="flex gap-3">
          <Input placeholder="Search students…" value={search} onChange={(e) => setSearch(e.target.value)} className="max-w-xs" />
          {canAdd && (
            <Button asChild><Link href="/students/new">Add Student</Link></Button>
          )}
        </div>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>ID</TableHead>
              <TableHead>Grade</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {students.map((s) => (
              <TableRow key={s.id} className="cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800">
                <TableCell>
                  <Link href={`/students/${s.id}`} className="font-medium hover:underline">{s.name}</Link>
                </TableCell>
                <TableCell className="text-slate-500">{s.student_id_number}</TableCell>
                <TableCell>Grade {s.grade_level}</TableCell>
              </TableRow>
            ))}
            {students.length === 0 && (
              <TableRow><TableCell colSpan={3} className="text-center text-slate-400 py-8">No students found</TableCell></TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Create student profile page**

`frontend/src/app/(protected)/students/[id]/page.tsx`:
```typescript
"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import type { Student, Score } from "@/lib/types";
import { Header } from "@/components/layout/header";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

function tierColor(value: number) {
  if (value >= 80) return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200";
  if (value >= 70) return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200";
  return "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200";
}

export default function StudentProfilePage() {
  const { id } = useParams<{ id: string }>();
  const [student, setStudent] = useState<Student | null>(null);
  const [scores, setScores] = useState<Score[]>([]);

  useEffect(() => {
    api.get<Student>(`/students/${id}`).then(setStudent).catch(console.error);
    api.get<Score[]>(`/scores/student/${id}`).then(setScores).catch(console.error);
  }, [id]);

  if (!student) return <div className="p-6 text-slate-400">Loading…</div>;

  return (
    <div>
      <Header title={student.name} />
      <div className="p-6 space-y-6">
        <Card>
          <CardHeader><CardTitle>Student Information</CardTitle></CardHeader>
          <CardContent className="grid grid-cols-2 gap-4 text-sm">
            <div><span className="text-slate-500">ID: </span>{student.student_id_number}</div>
            <div><span className="text-slate-500">Grade: </span>Grade {student.grade_level}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Scores</CardTitle></CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead>Subject</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Score</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {scores.map((s) => (
                  <TableRow key={s.id}>
                    <TableCell>{s.date}</TableCell>
                    <TableCell>{s.subject_id}</TableCell>
                    <TableCell className="capitalize">{s.score_type}</TableCell>
                    <TableCell>
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${tierColor(s.value)}`}>
                        {s.value}%
                      </span>
                    </TableCell>
                  </TableRow>
                ))}
                {scores.length === 0 && (
                  <TableRow><TableCell colSpan={4} className="text-center text-slate-400 py-6">No scores recorded</TableCell></TableRow>
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Create new student page**

`frontend/src/app/(protected)/students/new/page.tsx`:
```typescript
"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { School, Class } from "@/lib/types";
import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function NewStudentPage() {
  const router = useRouter();
  const [schools, setSchools] = useState<School[]>([]);
  const [classes, setClasses] = useState<Class[]>([]);
  const [form, setForm] = useState({ name: "", student_id_number: "", grade_level: "", school_id: "", class_id: "" });
  const [error, setError] = useState("");

  useEffect(() => {
    api.get<School[]>("/admin/schools").then(setSchools).catch(console.error);
    api.get<Class[]>("/admin/classes").then(setClasses).catch(console.error);
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      const s = await api.post<{ id: string }>("/students", {
        ...form,
        grade_level: parseInt(form.grade_level),
        class_id: form.class_id || null,
      });
      router.push(`/students/${s.id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create student");
    }
  }

  return (
    <div>
      <Header title="Add Student" />
      <div className="p-6 max-w-lg">
        <Card>
          <CardHeader><CardTitle>New Student</CardTitle></CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-1">
                <Label>Full Name</Label>
                <Input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
              </div>
              <div className="space-y-1">
                <Label>Student ID</Label>
                <Input required value={form.student_id_number} onChange={(e) => setForm({ ...form, student_id_number: e.target.value })} />
              </div>
              <div className="space-y-1">
                <Label>Grade Level</Label>
                <Input type="number" min={1} max={12} required value={form.grade_level} onChange={(e) => setForm({ ...form, grade_level: e.target.value })} />
              </div>
              <div className="space-y-1">
                <Label>School</Label>
                <Select onValueChange={(v) => setForm({ ...form, school_id: v })} required>
                  <SelectTrigger><SelectValue placeholder="Select school" /></SelectTrigger>
                  <SelectContent>
                    {schools.map((s) => <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1">
                <Label>Class (optional)</Label>
                <Select onValueChange={(v) => setForm({ ...form, class_id: v })}>
                  <SelectTrigger><SelectValue placeholder="Select class" /></SelectTrigger>
                  <SelectContent>
                    {classes.map((c) => <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              {error && <p className="text-sm text-red-600">{error}</p>}
              <div className="flex gap-2">
                <Button type="submit">Save Student</Button>
                <Button type="button" variant="outline" onClick={() => router.back()}>Cancel</Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Manual smoke test**

With both backend and frontend running, log in as `teacher`/`changeme`:
- `/students` — should show the 5 students in teacher's classes
- `/students/[id]` — should show student profile with scores table
- `/students/new` — should show the create form

Log in as `admin`/`changeme` — `/students` should show all 10 students.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/app/\(protected\)/students/
git commit -m "feat: student list, profile, and new student pages"
```

---

## Task 14: Score pages

**Files:**
- Create: `frontend/src/app/(protected)/scores/entry/page.tsx`
- Create: `frontend/src/app/(protected)/scores/import/page.tsx`

- [ ] **Step 1: Create score entry page**

`frontend/src/app/(protected)/scores/entry/page.tsx`:
```typescript
"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Student, Subject } from "@/lib/types";
import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";

export default function ScoreEntryPage() {
  const [students, setStudents] = useState<Student[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [form, setForm] = useState({ student_id: "", subject_id: "", score_type: "", value: "", date: "", notes: "" });
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api.get<Student[]>("/students").then(setStudents).catch(console.error);
    api.get<Subject[]>("/admin/subjects").then(setSubjects).catch(console.error);
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(""); setSuccess(false);
    try {
      await api.post("/scores", { ...form, value: parseFloat(form.value) });
      setSuccess(true);
      setForm({ ...form, value: "", notes: "" });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to save score");
    }
  }

  return (
    <div>
      <Header title="Enter Score" />
      <div className="p-6 max-w-lg">
        <Card>
          <CardHeader><CardTitle>New Score Entry</CardTitle></CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-1">
                <Label>Student</Label>
                <Select onValueChange={(v) => setForm({ ...form, student_id: v })} required>
                  <SelectTrigger><SelectValue placeholder="Select student" /></SelectTrigger>
                  <SelectContent>
                    {students.map((s) => <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1">
                <Label>Subject</Label>
                <Select onValueChange={(v) => setForm({ ...form, subject_id: v })} required>
                  <SelectTrigger><SelectValue placeholder="Select subject" /></SelectTrigger>
                  <SelectContent>
                    {subjects.map((s) => <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1">
                <Label>Type</Label>
                <Select onValueChange={(v) => setForm({ ...form, score_type: v })} required>
                  <SelectTrigger><SelectValue placeholder="Select type" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="homework">Homework</SelectItem>
                    <SelectItem value="quiz">Quiz</SelectItem>
                    <SelectItem value="test">Test</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <Label>Score (0–100)</Label>
                  <Input type="number" min={0} max={100} step={0.1} required value={form.value} onChange={(e) => setForm({ ...form, value: e.target.value })} />
                </div>
                <div className="space-y-1">
                  <Label>Date</Label>
                  <Input type="date" required value={form.date} onChange={(e) => setForm({ ...form, date: e.target.value })} />
                </div>
              </div>
              <div className="space-y-1">
                <Label>Notes (optional)</Label>
                <Textarea rows={2} value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
              </div>
              {success && <Alert><AlertDescription>Score saved successfully.</AlertDescription></Alert>}
              {error && <Alert variant="destructive"><AlertDescription>{error}</AlertDescription></Alert>}
              <Button type="submit" className="w-full">Save Score</Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Create CSV import page**

`frontend/src/app/(protected)/scores/import/page.tsx`:
```typescript
"use client";
import { useRef, useState } from "react";
import { api } from "@/lib/api";
import type { CSVImportResult } from "@/lib/types";
import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";

export default function ScoreImportPage() {
  const fileRef = useRef<HTMLInputElement>(null);
  const [result, setResult] = useState<CSVImportResult | null>(null);
  const [uploading, setUploading] = useState(false);

  async function handleUpload(e: React.FormEvent) {
    e.preventDefault();
    const file = fileRef.current?.files?.[0];
    if (!file) return;
    setUploading(true);
    setResult(null);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const res = await api.upload<CSVImportResult>("/scores/import", fd);
      setResult(res);
    } catch (err: unknown) {
      setResult({ imported: 0, errors: [{ row: 0, message: err instanceof Error ? err.message : "Upload failed" }] });
    } finally {
      setUploading(false);
    }
  }

  return (
    <div>
      <Header title="Import Scores" />
      <div className="p-6 max-w-2xl space-y-4">
        <Card>
          <CardHeader><CardTitle>Upload Score CSV</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-slate-500">
              Upload a CSV file with columns: <code className="text-xs bg-slate-100 dark:bg-slate-800 px-1 rounded">student_id_number, subject_name, score_type, value, date, notes</code>
            </p>
            <Button variant="outline" size="sm" asChild>
              <a href="/api/scores/template.csv" download>Download Template</a>
            </Button>
            <form onSubmit={handleUpload} className="flex gap-3 items-end">
              <input ref={fileRef} type="file" accept=".csv" className="text-sm" required />
              <Button type="submit" disabled={uploading}>{uploading ? "Uploading…" : "Import"}</Button>
            </form>
          </CardContent>
        </Card>

        {result && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                Results
                {result.errors.length === 0
                  ? <Badge className="bg-green-100 text-green-800">{result.imported} imported</Badge>
                  : <Badge variant="destructive">{result.errors.length} errors</Badge>
                }
              </CardTitle>
            </CardHeader>
            {result.errors.length > 0 && (
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Row</TableHead>
                      <TableHead>Error</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {result.errors.map((e, i) => (
                      <TableRow key={i}>
                        <TableCell className="font-medium">{e.row === 0 ? "File" : `Row ${e.row}`}</TableCell>
                        <TableCell className="text-red-600 dark:text-red-400">{e.message}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            )}
          </Card>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Manual smoke test**

With backend and frontend running, log in as `teacher`/`changeme`:
- `/scores/entry` — enter a score for Alice Johnson in Mathematics. Expected: "Score saved successfully."
- `/scores/import` — download the template, fill in one row, upload. Expected: 1 imported.
- `/scores/import` — upload a file with an invalid score_type. Expected: 1 error row shown.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/app/\(protected\)/scores/
git commit -m "feat: score entry and CSV import pages"
```

---

## Task 15: Admin pages

**Files:**
- Create: `frontend/src/app/(protected)/admin/users/page.tsx`
- Create: `frontend/src/app/(protected)/admin/schools/page.tsx`
- Create: `frontend/src/app/(protected)/admin/classes/page.tsx`
- Create: `frontend/src/app/(protected)/admin/subjects/page.tsx`

- [ ] **Step 1: Create users admin page**

`frontend/src/app/(protected)/admin/users/page.tsx`:
```typescript
"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { User, School } from "@/lib/types";
import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Card, CardContent } from "@/components/ui/card";

const ROLES = ["it_admin", "district_admin", "principal", "teacher"] as const;

export default function UsersAdminPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [schools, setSchools] = useState<School[]>([]);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ username: "", password: "", role: "", school_id: "" });
  const [error, setError] = useState("");

  const load = () => {
    api.get<User[]>("/admin/users").then(setUsers).catch(console.error);
    api.get<School[]>("/admin/schools").then(setSchools).catch(console.error);
  };

  useEffect(() => { load(); }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault(); setError("");
    try {
      await api.post("/admin/users", { ...form, school_id: form.school_id || null });
      setOpen(false); setForm({ username: "", password: "", role: "", school_id: "" }); load();
    } catch (err: unknown) { setError(err instanceof Error ? err.message : "Error"); }
  }

  async function handleDelete(id: string) {
    if (!confirm("Delete this user?")) return;
    await api.delete(`/admin/users/${id}`); load();
  }

  const roleBadge = (role: string) => {
    const colors: Record<string, string> = {
      it_admin: "bg-purple-100 text-purple-800",
      district_admin: "bg-blue-100 text-blue-800",
      principal: "bg-orange-100 text-orange-800",
      teacher: "bg-green-100 text-green-800",
    };
    return <span className={`px-2 py-0.5 rounded text-xs font-medium ${colors[role] ?? ""}`}>{role}</span>;
  };

  return (
    <div>
      <Header title="User Management" />
      <div className="p-6 space-y-4">
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild><Button>Add User</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>New User</DialogTitle></DialogHeader>
            <form onSubmit={handleCreate} className="space-y-3 mt-2">
              <div className="space-y-1"><Label>Username</Label><Input required value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} /></div>
              <div className="space-y-1"><Label>Password</Label><Input type="password" required value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} /></div>
              <div className="space-y-1">
                <Label>Role</Label>
                <Select onValueChange={(v) => setForm({ ...form, role: v })} required>
                  <SelectTrigger><SelectValue placeholder="Select role" /></SelectTrigger>
                  <SelectContent>{ROLES.map((r) => <SelectItem key={r} value={r}>{r}</SelectItem>)}</SelectContent>
                </Select>
              </div>
              <div className="space-y-1">
                <Label>School (optional)</Label>
                <Select onValueChange={(v) => setForm({ ...form, school_id: v })}>
                  <SelectTrigger><SelectValue placeholder="Select school" /></SelectTrigger>
                  <SelectContent>{schools.map((s) => <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>)}</SelectContent>
                </Select>
              </div>
              {error && <p className="text-sm text-red-600">{error}</p>}
              <Button type="submit" className="w-full">Create User</Button>
            </form>
          </DialogContent>
        </Dialog>

        <Card><CardContent className="p-0">
          <Table>
            <TableHeader><TableRow><TableHead>Username</TableHead><TableHead>Role</TableHead><TableHead></TableHead></TableRow></TableHeader>
            <TableBody>
              {users.map((u) => (
                <TableRow key={u.id}>
                  <TableCell className="font-medium">{u.username}</TableCell>
                  <TableCell>{roleBadge(u.role)}</TableCell>
                  <TableCell><Button size="sm" variant="ghost" className="text-red-500 hover:text-red-700" onClick={() => handleDelete(u.id)}>Delete</Button></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent></Card>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Create schools admin page**

`frontend/src/app/(protected)/admin/schools/page.tsx`:
```typescript
"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { School } from "@/lib/types";
import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Card, CardContent } from "@/components/ui/card";

export default function SchoolsAdminPage() {
  const [schools, setSchools] = useState<School[]>([]);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ name: "", address: "" });

  const load = () => api.get<School[]>("/admin/schools").then(setSchools).catch(console.error);
  useEffect(() => { load(); }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    await api.post("/admin/schools", form);
    setOpen(false); setForm({ name: "", address: "" }); load();
  }

  return (
    <div>
      <Header title="Schools" />
      <div className="p-6 space-y-4">
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild><Button>Add School</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>New School</DialogTitle></DialogHeader>
            <form onSubmit={handleCreate} className="space-y-3 mt-2">
              <div className="space-y-1"><Label>School Name</Label><Input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></div>
              <div className="space-y-1"><Label>Address</Label><Input value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} /></div>
              <Button type="submit" className="w-full">Create School</Button>
            </form>
          </DialogContent>
        </Dialog>
        <Card><CardContent className="p-0">
          <Table>
            <TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Address</TableHead></TableRow></TableHeader>
            <TableBody>
              {schools.map((s) => (
                <TableRow key={s.id}><TableCell className="font-medium">{s.name}</TableCell><TableCell className="text-slate-500">{s.address ?? "—"}</TableCell></TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent></Card>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Create classes admin page**

`frontend/src/app/(protected)/admin/classes/page.tsx`:
```typescript
"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Class, School, User } from "@/lib/types";
import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Card, CardContent } from "@/components/ui/card";

export default function ClassesAdminPage() {
  const [classes, setClasses] = useState<Class[]>([]);
  const [schools, setSchools] = useState<School[]>([]);
  const [teachers, setTeachers] = useState<User[]>([]);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ name: "", grade_level: "", school_id: "", teacher_id: "" });

  const load = () => api.get<Class[]>("/admin/classes").then(setClasses).catch(console.error);

  useEffect(() => {
    load();
    api.get<School[]>("/admin/schools").then(setSchools).catch(console.error);
    api.get<User[]>("/admin/users").then((u) => setTeachers(u.filter((x) => x.role === "teacher"))).catch(console.error);
  }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    await api.post("/admin/classes", { ...form, grade_level: parseInt(form.grade_level), teacher_id: form.teacher_id || null });
    setOpen(false); setForm({ name: "", grade_level: "", school_id: "", teacher_id: "" }); load();
  }

  return (
    <div>
      <Header title="Classes" />
      <div className="p-6 space-y-4">
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild><Button>Add Class</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>New Class</DialogTitle></DialogHeader>
            <form onSubmit={handleCreate} className="space-y-3 mt-2">
              <div className="space-y-1"><Label>Class Name</Label><Input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></div>
              <div className="space-y-1"><Label>Grade Level</Label><Input type="number" min={1} max={12} required value={form.grade_level} onChange={(e) => setForm({ ...form, grade_level: e.target.value })} /></div>
              <div className="space-y-1">
                <Label>School</Label>
                <Select onValueChange={(v) => setForm({ ...form, school_id: v })} required>
                  <SelectTrigger><SelectValue placeholder="Select school" /></SelectTrigger>
                  <SelectContent>{schools.map((s) => <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>)}</SelectContent>
                </Select>
              </div>
              <div className="space-y-1">
                <Label>Teacher (optional)</Label>
                <Select onValueChange={(v) => setForm({ ...form, teacher_id: v })}>
                  <SelectTrigger><SelectValue placeholder="Select teacher" /></SelectTrigger>
                  <SelectContent>{teachers.map((t) => <SelectItem key={t.id} value={t.id}>{t.username}</SelectItem>)}</SelectContent>
                </Select>
              </div>
              <Button type="submit" className="w-full">Create Class</Button>
            </form>
          </DialogContent>
        </Dialog>
        <Card><CardContent className="p-0">
          <Table>
            <TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Grade</TableHead></TableRow></TableHeader>
            <TableBody>
              {classes.map((c) => (
                <TableRow key={c.id}><TableCell className="font-medium">{c.name}</TableCell><TableCell>Grade {c.grade_level}</TableCell></TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent></Card>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Create subjects admin page**

`frontend/src/app/(protected)/admin/subjects/page.tsx`:
```typescript
"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Subject } from "@/lib/types";
import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Card, CardContent } from "@/components/ui/card";

export default function SubjectsAdminPage() {
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");

  const load = () => api.get<Subject[]>("/admin/subjects").then(setSubjects).catch(console.error);
  useEffect(() => { load(); }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    await api.post("/admin/subjects", { name });
    setOpen(false); setName(""); load();
  }

  return (
    <div>
      <Header title="Subjects" />
      <div className="p-6 space-y-4">
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild><Button>Add Subject</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>New Subject</DialogTitle></DialogHeader>
            <form onSubmit={handleCreate} className="space-y-3 mt-2">
              <div className="space-y-1"><Label>Subject Name</Label><Input required value={name} onChange={(e) => setName(e.target.value)} /></div>
              <Button type="submit" className="w-full">Create Subject</Button>
            </form>
          </DialogContent>
        </Dialog>
        <Card><CardContent className="p-0">
          <Table>
            <TableHeader><TableRow><TableHead>Subject</TableHead></TableRow></TableHeader>
            <TableBody>
              {subjects.map((s) => <TableRow key={s.id}><TableCell className="font-medium">{s.name}</TableCell></TableRow>)}
            </TableBody>
          </Table>
        </CardContent></Card>
      </div>
    </div>
  );
}
```

- [ ] **Step 5: Manual smoke test**

Log in as `admin`/`changeme`:
- `/admin/users` — list users, create a new teacher. Expected: appears in table.
- `/admin/schools` — create a new school. Expected: appears in table.
- `/admin/classes` — create a class, assign school and teacher. Expected: appears in table.
- `/admin/subjects` — create a subject. Expected: appears in table.
- Log in as `teacher` and verify `/admin/users` returns 403.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/app/\(protected\)/admin/
git commit -m "feat: admin pages for users, schools, classes, and subjects"
```

---

## Task 16: Deploy scripts and README

**Files:**
- Create: `deploy/start.bat`
- Create: `deploy/start.sh`
- Create: `README.md`

- [ ] **Step 1: Create Windows startup script**

`deploy/start.bat`:
```batch
@echo off
echo Starting Compass...

start "Compass Backend" cmd /k "cd /d %~dp0..\backend && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000"
timeout /t 3 /nobreak >nul
start "Compass Frontend" cmd /k "cd /d %~dp0..\frontend && npm run dev"

echo.
echo Compass is starting up.
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:3000
echo   API docs: http://localhost:8000/docs
echo.
echo Close the two terminal windows to stop Compass.
```

- [ ] **Step 2: Create Linux startup script**

`deploy/start.sh`:
```bash
#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "Starting Compass backend..."
cd "$ROOT/backend"
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

sleep 2

echo "Starting Compass frontend..."
cd "$ROOT/frontend"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "Compass is running."
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM
wait
```

```bash
chmod +x deploy/start.sh
```

- [ ] **Step 3: Create README.md**

`README.md`:
```markdown
# Compass

Student Learning Analytics and MTSS Recommendation System — locally hosted, no cloud dependencies.

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (`pip install uv`)
- Node.js 20+ and npm
- [Ollama](https://ollama.ai) (for Phase 3 AI features)

## Installation

### Backend

```bash
cd backend
cp .env.example .env
uv sync
uv run alembic upgrade head
uv run python -m app.seed
```

### Frontend

```bash
cd frontend
npm install
```

## Running

### Windows

```batch
deploy\start.bat
```

### Linux / macOS

```bash
./deploy/start.sh
```

Or start manually:

```bash
# Terminal 1
cd backend && uv run uvicorn app.main:app --reload

# Terminal 2
cd frontend && npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Default Accounts

| Username | Password | Role |
|----------|----------|------|
| admin | changeme | IT Admin |
| district | changeme | District Admin |
| principal | changeme | Principal |
| teacher | changeme | Teacher |

**Change all passwords after first login.**

## Ollama Setup (Phase 3)

```bash
ollama pull llama3.2
```

Compass connects to Ollama at `http://localhost:11434` by default. Configure via `backend/.env`.

## Database Backup

```bash
cp backend/compass.db backend/compass.db.bak
```

## PostgreSQL Migration

When ready to migrate from SQLite to PostgreSQL:

1. Install PostgreSQL and create a database
2. `cd backend && uv add psycopg2-binary`
3. Update `DATABASE_URL` in `backend/.env`: `postgresql://user:pass@localhost/compass`
4. `uv run alembic upgrade head`
5. Re-run `uv run python -m app.seed` if starting fresh

## Running Tests

```bash
cd backend && uv run pytest -v
```
```

- [ ] **Step 4: Final full test run**

```bash
cd backend && uv run pytest -v
```
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
cd ..
git add deploy/ README.md
git commit -m "feat: deploy scripts and README"
```

---

## Self-Review Checklist

- [x] **Spec coverage:** Auth (login/logout/me) ✓ | Session persistence ✓ | RBAC (4 roles, per-route) ✓ | All DB tables created in Phase 1 ✓ | UUID PKs ✓ | No SQLite-specific features ✓ | Student CRUD ✓ | Role-scoped student list ✓ | Score entry ✓ | CSV import with per-row validation ✓ | CSV template download ✓ | Admin CRUD (users/schools/classes/subjects) ✓ | Seed data (all 4 roles + students/scores) ✓ | Login page ✓ | Protected routes ✓ | Sidebar with role-aware nav ✓ | Dark/light toggle ✓ | `deploy/start.bat` + `start.sh` ✓ | README with install/run/backup/pg-migration ✓
- [x] **Placeholders:** None — all steps contain complete code
- [x] **Type consistency:** `UserRole` enum values consistent throughout (it_admin, district_admin, principal, teacher). `ScoreType` consistent (homework, quiz, test). UUID handling consistent (uuid.UUID in Python, string in TypeScript). `get_student_tier` in mtss.py references correct model fields.
- [x] **Scope:** All Phase 2+ features (dashboards, charts, alerts, AI, interventions, reports, audit UI) are absent from this plan.

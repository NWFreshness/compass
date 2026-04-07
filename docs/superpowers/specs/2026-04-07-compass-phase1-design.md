# Compass — Phase 1 Design Spec

**Date:** 2026-04-07  
**Scope:** Phase 1 — Auth, data model, student management, score entry, CSV import, admin tools  
**Approach:** Option A (strict phase boundaries) — each phase gets its own spec → plan → build cycle  
**Implementation note:** Use `superpowers:subagent-driven-development` during build to parallelize independent tasks

---

## Context

Compass is a locally-hosted Student Learning Analytics and MTSS Recommendation System. It runs entirely on-premises with no cloud dependencies. Built with Next.js (frontend) and FastAPI (backend).

- **Deployment target:** Windows Server (primary), Linux (secondary)
- **Database:** SQLite for MVP, designed for PostgreSQL migration (100+ concurrent users anticipated)
- **Sessions:** SQLite-persisted, HttpOnly secure cookies, 24-hour expiry
- **AI:** Ollama at `localhost:11434`, model `llama3.2` (Phase 3)

---

## Repository Structure

```
compass/
  backend/
    pyproject.toml         # uv-managed
    .env.example
    alembic/
    app/
      main.py              # FastAPI app, router registration
      config.py            # pydantic-settings, reads .env
      db.py                # SQLAlchemy engine, get_db dependency
      models/              # one file per domain
      schemas/             # one file per domain (Pydantic)
      routes/              # one file per domain
      services/
        auth.py            # password hashing, session management
        mtss.py            # tier calculation logic
      middleware/          # get_current_user, require_role deps
      seed.py              # seeds all roles + sample data
      tests/
        conftest.py        # in-memory SQLite DB per test session
  frontend/
    package.json
    .env.local.example
    src/
      app/                 # Next.js App Router pages
      components/          # shared UI components
      lib/
        api.ts             # typed fetch wrapper
        auth.ts            # auth context helpers
      styles/
  deploy/
    start.bat              # Windows: starts backend + frontend
    start.sh               # Linux fallback
  docs/
    superpowers/specs/
```

**Frontend proxies `/api/*` to backend** via `next.config.ts` rewrites — no CORS config needed.  
Backend: `http://localhost:8000` | Frontend: `http://localhost:3000`

---

## Tech Stack

| Layer | Choice |
|-------|--------|
| Frontend | Next.js (App Router), TypeScript, Tailwind CSS, shadcn/ui, Recharts |
| Backend | FastAPI, SQLAlchemy, Alembic, Pydantic, passlib[bcrypt], pydantic-settings |
| Database | SQLite (MVP) — PostgreSQL-ready (UUID PKs, no SQLite-specific features) |
| Package managers | `uv` (Python), `npm` (Node) |

**PostgreSQL migration path:** swap `DATABASE_URL` in `.env` and `uv add psycopg2-binary`. No model changes required.

---

## Database Schema

All primary keys are UUIDs. All foreign keys enforced. Alembic manages all migrations. **All Phase 1–4 tables are created in Phase 1** to avoid destructive migrations later.

| Table | Key columns |
|-------|-------------|
| `schools` | id, name, address |
| `users` | id, username, hashed_password, role, school_id (nullable) |
| `sessions` | id, user_id, expires_at |
| `classes` | id, name, grade_level, school_id, teacher_id |
| `students` | id, name, student_id_number, grade_level, school_id, class_id |
| `subjects` | id, name |
| `scores` | id, student_id, subject_id, score_type (homework/quiz/test), value, date, notes |
| `benchmarks` | id, grade_level, subject_id, tier1_min, tier2_min |
| `ai_recs` | id, student_id (nullable), class_id (nullable), prompt, response, created_at, created_by |
| `interventions` | id, student_id, teacher_id, strategy, description, start_date, outcome_notes, status |
| `audit_log` | id, user_id, action, entity_type, entity_id, timestamp |

---

## Authentication & Sessions

### Flow
1. `POST /api/auth/login` — validates credentials, creates `sessions` row (24hr expiry), sets `session_id` HttpOnly secure cookie
2. `get_current_user` FastAPI dependency — reads cookie, validates session, returns user or raises 401
3. `POST /api/auth/logout` — deletes session row, clears cookie
4. `GET /api/auth/me` — returns `{id, username, role, school_id}`

### RBAC
- Roles: `it_admin`, `district_admin`, `principal`, `teacher`
- Enforced via `require_role(*roles)` dependency factory declared per-route
- No middleware magic — explicit and auditable

### Frontend Auth
- `/login` is the only public route
- Root layout calls `GET /api/auth/me` on mount, redirects to `/login` on 401
- Role stored in React context, drives sidebar link visibility

---

## Phase 1 API Routes

### Auth
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`

### Students
- `GET /api/students` — role-scoped (teacher: own class; principal: school; district_admin/it_admin: all)
- `GET /api/students/{id}`
- `POST /api/students`
- `PATCH /api/students/{id}`

### Scores
- `POST /api/scores`
- `POST /api/scores/import` — CSV bulk import with server-side validation
- `GET /api/scores/student/{id}`
- `GET /api/scores/template.csv` — downloadable CSV template

### Admin (IT Admin only)
- `GET /api/admin/users`, `POST /api/admin/users`
- `PATCH /api/admin/users/{id}`, `DELETE /api/admin/users/{id}`
- `GET /api/admin/schools`, `POST /api/admin/schools`
- `GET /api/admin/classes`, `POST /api/admin/classes`
- `GET /api/admin/subjects`, `POST /api/admin/subjects`

All list endpoints support `?search=` and `?page=` from day one.

---

## Frontend Pages (Phase 1)

### Public
- `/login` — username/password form, redirects to role-appropriate landing on success

### Shared Layout
- Sidebar with role-filtered nav links
- Dark/light mode toggle
- Logout button

### Students
- `/students` — searchable, filterable, role-scoped table
- `/students/[id]` — profile: basic info + scores table (no charts — Phase 2)
- `/students/new` — create student form

### Scores
- `/scores/entry` — single score entry (student, subject, type, value, date, notes)
- `/scores/import` — CSV upload with per-row validation feedback table

### Admin (IT Admin only)
- `/admin/users` — user CRUD with role and school assignment
- `/admin/schools` — school CRUD
- `/admin/classes` — class CRUD with teacher assignment
- `/admin/subjects` — subject CRUD

---

## Seed Data

Run via `uv run python -m app.seed`. Idempotent (safe to re-run).

| Seeded entity | Detail |
|---------------|--------|
| Schools | 2 schools in 1 district |
| Users | `admin` (it_admin), `district` (district_admin), `principal` (principal), `teacher` (teacher) — all password `changeme` |
| Classes | 2 classes assigned to teacher |
| Students | 10 students spread across classes |
| Subjects | 3 subjects (e.g. Math, Reading, Science) |
| Scores | ~30 scores across students/subjects, spread over recent dates |

---

## Testing

- **Backend:** `pytest` — `conftest.py` spins up in-memory SQLite DB per session
- **Covered:** auth flow, RBAC enforcement (wrong role → 403), CSV import validation, MTSS tier calculation
- **Frontend:** manual testing against seeded data (no automated tests in Phase 1)

---

## Startup Scripts

- `deploy/start.bat` — opens two windows: `uv run uvicorn app.main:app --reload` and `npm run dev`
- `deploy/start.sh` — same using `tmux` or background processes for Linux

---

## Out of Scope for Phase 1

- Dashboards and charts (Phase 2)
- MTSS alerts (Phase 2)
- AI recommendations (Phase 3)
- Intervention tracking (Phase 3)
- Reports / PDF / CSV exports (Phase 4)
- Audit log UI (Phase 4)

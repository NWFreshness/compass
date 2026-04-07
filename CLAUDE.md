# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Compass** is a locally-hosted Student Learning Analytics and MTSS (Multi-Tiered System of Supports) Recommendation System. It is a monorepo with a Next.js frontend and FastAPI backend. All data stays on-premises — no cloud services.

## Monorepo Structure

```
compass/
  frontend/        # Next.js + TypeScript
  backend/         # FastAPI + Python (uv)
  deploy/
  docs/
```

## Development Commands

### Backend

```bash
cd backend
uv run uvicorn app.main:app --reload        # start dev server
uv run pytest                               # run all tests
uv run pytest tests/test_foo.py::test_bar   # run a single test
uv run alembic upgrade head                 # apply migrations
uv run alembic revision --autogenerate -m "description"  # new migration
```

### Frontend

```bash
cd frontend
npm install
npm run dev          # start dev server (Next.js)
npm run build        # production build
npm run lint         # lint
```

## Architecture

### Backend (`backend/app/`)

- `main.py` — FastAPI app entrypoint, router registration, middleware
- `config.py` — settings (Ollama URL, model name, temperature, DB path)
- `db.py` — SQLAlchemy engine and session dependency
- `models/` — SQLAlchemy ORM models (schools, users, classes, students, subjects, scores, ai_recs, interventions, audit_log, benchmarks)
- `schemas/` — Pydantic request/response models
- `routes/` — FastAPI routers grouped by domain (auth, students, scores, ai, interventions, admin, reports, dashboard)
- `services/` — business logic: MTSS tier calculation, AI prompt building, Ollama calls, report generation
- `middleware/` — session auth, RBAC enforcement

**Session auth:** backend-managed sessions in secure cookies (no JWT). `GET /api/auth/me` returns current user and role.

**RBAC roles:** `it_admin` > `district_admin` > `principal` > `teacher`. Authorization is enforced server-side per route.

**AI flow:** frontend → FastAPI → Ollama (localhost:11434). FastAPI builds the prompt, calls Ollama, stores result in `ai_recs`, returns to frontend. Frontend never calls Ollama directly.

### Frontend (`frontend/src/`)

- `app/` — Next.js App Router pages: `login/`, `dashboard/`, `students/`, `students/[id]/`, `scores/`, `ai/`, `admin/`, `reports/`
- `components/` — shared UI components
- `lib/` — API client, auth helpers, MTSS utilities
- `styles/` — Tailwind config and globals

All routes except `/login` are protected. Role-aware navigation hides sections the current user cannot access.

## Key Business Logic

### MTSS Tier Thresholds (backend only, never frontend)

- Tier 1 (green): avg score >= 80
- Tier 2 (yellow): avg score 70–79
- Tier 3 (red): avg score < 70

Benchmarks can be overridden per grade/subject via the `benchmarks` table.

### Score Color Coding

- Green: >= 80%
- Yellow: 70–79%
- Red: < 70%

## Tech Stack

| Layer | Choice |
|-------|--------|
| Frontend | Next.js, TypeScript, Tailwind CSS, Recharts or Chart.js |
| Backend | FastAPI, SQLAlchemy, Alembic, Pydantic, passlib[bcrypt] |
| Database | SQLite (MVP), designed for later PostgreSQL migration |
| AI | Ollama at `localhost:11434`, default model `llama3.2` |
| Package mgr | `uv` (Python), `npm` (Node) |

## API Base Path

All backend endpoints are under `/api`. Key groups: `/api/auth`, `/api/dashboard`, `/api/students`, `/api/scores`, `/api/ai`, `/api/interventions`, `/api/admin`, `/api/reports`.

## Implementation Order

Build in phases per SPEC.md: Phase 1 (auth + data model + score entry) → Phase 2 (dashboards + alerts) → Phase 3 (AI + interventions + benchmarks) → Phase 4 (reports + audit log + polish).

# Compass — Phase 3C Design Spec

**Date:** 2026-04-13
**Scope:** Phase 3C — benchmark configuration and benchmark-aware tier administration
**Approach:** admin-managed `grade_level + subject` benchmark CRUD used consistently by MTSS, dashboards, and AI analysis

---

## Context

The backend already has a `Benchmark` model and the MTSS service already consults benchmark overrides when a subject-specific tier is computed.

What is missing:

- benchmark CRUD APIs
- benchmark admin UI
- explicit validation and uniqueness guarantees
- broader use of benchmark-aware tier explanation in the application

---

## Goals

- Allow IT Admin and District Admin to create, update, and delete benchmarks
- Keep benchmarks scoped to `grade_level + subject`
- Enforce threshold validity consistently
- Ensure dashboards and AI analysis use the configured thresholds

---

## Backend

### New files

| File | Responsibility |
|------|---------------|
| `app/schemas/benchmark.py` | Benchmark create/update/response models |
| `app/routes/benchmarks.py` | Benchmark CRUD endpoints |
| `app/tests/test_benchmarks.py` | Benchmark CRUD and validation tests |

### Modified files

| File | Change |
|------|--------|
| `app/models/subject.py` | Add uniqueness constraint for `grade_level + subject_id` |
| `app/main.py` | Register `benchmarks_router` |
| `app/routes/admin.py` | Remove benchmark responsibility from future admin catch-all scope to keep it isolated |
| `app/services/mtss.py` | Keep benchmark resolution centralized and reusable for dashboards/AI |

### Validation rules

- one row per `grade_level + subject_id`
- `tier1_min` must be greater than or equal to `tier2_min`
- both thresholds must be between `0` and `100`
- delete is allowed only for IT Admin and District Admin

### Endpoints

#### `GET /api/benchmarks`

List benchmarks, optionally filtered by grade or subject.

#### `POST /api/benchmarks`

Create a benchmark row for a grade/subject pair.

#### `PATCH /api/benchmarks/{benchmark_id}`

Update thresholds.

#### `DELETE /api/benchmarks/{benchmark_id}`

Remove a benchmark override and fall back to default MTSS thresholds.

Roles:

- `it_admin`, `district_admin` may create/update/delete
- `principal`, `teacher` denied

---

## Frontend

### New files

| File | Responsibility |
|------|---------------|
| `src/app/(protected)/admin/benchmarks/page.tsx` | Benchmark management page |
| `src/components/admin/BenchmarkForm.tsx` | Create/edit benchmark form |

### Modified files

| File | Change |
|------|--------|
| `src/components/layout/sidebar.tsx` | Add benchmark nav item for IT Admin and District Admin |
| `src/lib/types.ts` | Add benchmark interfaces |

### UX

Benchmark page:

- table of current benchmark overrides
- create/edit modal or inline form
- filters by grade and subject
- clear indication that missing rows fall back to default thresholds

Educator-facing use:

- dashboards and AI features do not need direct benchmark editing controls
- when tier logic is displayed or explained, the backend-derived result should already reflect active overrides

---

## Testing

`app/tests/test_benchmarks.py` should cover:

- create benchmark as IT Admin
- create benchmark as District Admin
- reject teacher/principal writes
- reject duplicates for the same grade and subject
- reject invalid threshold ordering
- delete benchmark and verify fallback behavior in MTSS calculations

Frontend verification should cover:

- benchmark list rendering
- form validation
- successful create/edit/delete flows
- nav visibility by role

---

## Out of Scope for Phase 3C

- school-specific benchmark overrides
- benchmark approval workflow
- benchmark version history UI
- bulk CSV benchmark import

---

## Implementation Tasks

- [ ] **Task 1: Benchmark schemas and model validation** — add `app/schemas/benchmark.py`; update `app/models/subject.py`
- [ ] **Task 2: Benchmark routes and tests** — add `app/routes/benchmarks.py`, register router, implement `app/tests/test_benchmarks.py`
- [ ] **Task 3: Frontend benchmark types and admin page** — extend `src/lib/types.ts`; add benchmark admin UI
- [ ] **Task 4: Navigation and benchmark-aware UX integration** — update sidebar and confirm benchmark-aware tier behavior remains centralized

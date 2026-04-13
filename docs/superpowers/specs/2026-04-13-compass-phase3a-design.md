# Compass — Phase 3A Design Spec

**Date:** 2026-04-13
**Scope:** Phase 3A — AI analysis, recommendation generation, and recommendation history
**Approach:** Embed AI actions in existing student and dashboard workflows; store immutable recommendation snapshots

---

## Context

Phase 1 delivered auth, student and score management, and admin CRUD.

Phase 2 delivered dashboards and at-risk visibility.

The backend already contains:

- `app/models/ai_rec.py`
- `app/models/subject.py` benchmark support
- `app/services/mtss.py` benchmark-aware tier calculation

Phase 3A adds the missing application layer around those primitives:

- Ollama-backed analysis services
- AI API routes
- immutable recommendation snapshot storage
- educator-facing analysis actions and history views

No browser code may call Ollama directly.

---

## Goals

- Allow authorized users to analyze an individual student
- Allow authorized users to analyze a class
- Persist each analysis as a new immutable history entry
- Show recommendation history inline where educators already work
- Use benchmark-aware MTSS logic when building AI input summaries

---

## Backend

### New files

| File | Responsibility |
|------|---------------|
| `app/schemas/ai.py` | Request/response models for student analysis, class analysis, and history entries |
| `app/services/ollama.py` | Local Ollama client wrapper, model config, timeout/error handling |
| `app/services/ai_analysis.py` | Snapshot building, prompt construction, Ollama orchestration, persistence |
| `app/routes/ai.py` | Student/class analysis endpoints and history endpoints |
| `app/tests/test_ai.py` | Route, service, and RBAC tests for AI analysis/history |

### Modified files

| File | Change |
|------|--------|
| `app/config.py` | Add Ollama base URL, model name, temperature, and timeout settings |
| `app/main.py` | Register `ai_router` |
| `app/models/ai_rec.py` | Expand stored fields for immutable snapshot metadata and target labeling |

### `ai_recs` storage design

Each recommendation row stores:

- target type: `student` or `class`
- `student_id` or `class_id`
- `created_by`
- model name
- temperature
- prompt
- raw response
- structured snapshot JSON used to build the prompt
- created timestamp

The snapshot must include the exact analysis inputs used at generation time, including:

- subject averages
- overall averages
- benchmark-aware tier results
- at-risk flags
- recent score samples used in the summary

This makes history auditable even if scores or benchmarks change later.

### Endpoints

#### `POST /api/ai/student/{student_id}/analyze`

Roles:

- `teacher` for students in their assigned classes
- `principal` for students in their school
- `district_admin`, `it_admin` for any student

Behavior:

- load scoped student data and scores
- compute subject and overall performance summaries
- compute tier results using existing MTSS service and current benchmarks
- build prompt
- call Ollama
- persist immutable history record
- return created recommendation

#### `GET /api/ai/student/{student_id}/history`

Returns newest-first recommendation history for that student, within the caller's allowed scope.

#### `POST /api/ai/class/{class_id}/analyze`

Roles:

- `teacher` for classes assigned to them
- `principal` for classes in their school
- `district_admin`, `it_admin` for any class

Behavior:

- aggregate class-level averages and tier distribution
- summarize at-risk concentration and subject strengths/weaknesses
- build prompt
- call Ollama
- persist immutable history record
- return created recommendation

#### `GET /api/ai/class/{class_id}/history`

Returns newest-first recommendation history for that class, within allowed scope.

### Ollama client behavior

The backend client must:

- read model name and temperature from config
- call local Ollama on port `11434` by default
- raise clear backend errors when Ollama is unavailable or times out
- never expose Ollama host details to the frontend

### Response shape

The API should return both raw response text and a parsed structured view:

- recommended MTSS tier
- curriculum recommendations
- intervention strategies
- rationale tied to actual score summary data

If the model output cannot be parsed into the structured shape, store the raw text and return a validation error message field while still preserving the history row for audit/debugging.

---

## Frontend

### New files

| File | Responsibility |
|------|---------------|
| `src/components/ai/AnalysisCard.tsx` | Shared result display for AI recommendations |
| `src/components/ai/AnalysisHistory.tsx` | Recommendation history list with snapshot metadata |
| `src/components/ai/AnalyzeButton.tsx` | Trigger UI with loading, disabled, and error states |

### Modified files

| File | Change |
|------|--------|
| `src/app/(protected)/students/[id]/page.tsx` | Add student analysis action and history section |
| `src/components/dashboard/TeacherDashboard.tsx` | Add class analysis action/history affordance per class card |
| `src/components/dashboard/PrincipalDashboard.tsx` | Add class analysis action/history affordance in class table |
| `src/components/dashboard/DistrictDashboard.tsx` | No direct analyze action in Phase 3A |
| `src/lib/types.ts` | Add AI analysis payload and history interfaces |

### UX

Student profile:

- show `Analyze Student` action near the profile summary
- display latest recommendation prominently
- show expandable history list below it

Class contexts:

- show `Analyze Class` action where the user is already viewing class performance
- latest recommendation appears inline for that class
- history is visible per class in a compact panel or expandable row

### Frontend scope rules

- Teachers only see analysis controls for their own students/classes
- Principals only for their school
- District/IT admins for all allowed student/class views

The frontend may hide controls for unsupported roles, but backend authorization remains authoritative.

---

## Prompt design

The prompt builder should be deterministic and based on backend-generated summaries, not raw unbounded score dumps.

Each prompt includes:

- target identity and context
- current benchmark-aware tier result
- summarized performance by subject
- recent score trend summary
- at-risk context
- explicit instruction to return:
  - recommended MTSS tier
  - curriculum recommendations
  - intervention strategies
  - rationale referencing the supplied score summary

---

## Testing

`app/tests/test_ai.py` should cover:

- student analysis allowed only within role scope
- class analysis allowed only within role scope
- student history scoped correctly
- class history scoped correctly
- benchmark-aware tier data appears in snapshot input
- one explicit analysis call creates one new history row
- Ollama failures return controlled backend errors
- immutable snapshot data persists even after later score changes

Frontend verification should cover:

- analysis button loading/error states
- student detail history rendering
- class-level result/history rendering
- no control shown when role lacks action capability in the current view

---

## Out of Scope for Phase 3A

- standalone `/ai` navigation section
- district-wide AI analysis
- automatic re-use of prior recommendations
- scheduled or background AI analysis jobs
- editing or deleting recommendation history

---

## Implementation Tasks

- [ ] **Task 1: AI schema and model updates** — extend `app/models/ai_rec.py`; add `app/schemas/ai.py`
- [ ] **Task 2: Ollama client and AI analysis service** — add `app/services/ollama.py` and `app/services/ai_analysis.py`
- [ ] **Task 3: AI routes and backend tests** — add `app/routes/ai.py`, register router, implement `app/tests/test_ai.py`
- [ ] **Task 4: Frontend AI types and shared UI** — add AI interfaces to `src/lib/types.ts`; create shared AI components
- [ ] **Task 5: Student AI workflow** — update `src/app/(protected)/students/[id]/page.tsx` with analyze action and history
- [ ] **Task 6: Class AI workflow** — update teacher/principal dashboard components with class analysis action and history

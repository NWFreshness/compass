# Compass — Phase 3B Design Spec

**Date:** 2026-04-13
**Scope:** Phase 3B — student and class intervention tracking
**Approach:** support one intervention target per record, surfaced inline in student and class workflows

---

## Context

The backend already includes `app/models/intervention.py`, but it currently supports only student-targeted interventions and has no routes, schemas, or frontend workflows.

Phase 3B expands interventions into a full feature:

- student-targeted interventions
- class-targeted interventions
- active/resolved tracking
- scoped visibility and editing

---

## Goals

- Allow educators to create interventions for a student or class
- Track intervention status and outcome notes over time
- Show active and resolved interventions inline in relevant views
- Keep target rules explicit: each record belongs to exactly one target

---

## Backend

### New files

| File | Responsibility |
|------|---------------|
| `app/schemas/intervention.py` | Intervention create/update/response models |
| `app/routes/interventions.py` | List, create, and update endpoints with scope checks |
| `app/tests/test_interventions.py` | Intervention route and RBAC tests |

### Modified files

| File | Change |
|------|--------|
| `app/models/intervention.py` | Expand model to support `class_id` target and one-target validation |
| `app/main.py` | Register `interventions_router` |

### Data model rules

Each intervention record must have:

- exactly one target:
  - `student_id`, or
  - `class_id`
- `teacher_id` as the creating educator
- strategy
- description
- start date
- outcome notes
- status: `active` or `resolved`

Validation rules:

- reject rows with both `student_id` and `class_id`
- reject rows with neither target
- teachers can create/update only within their assigned scope
- principals only within their school
- district/IT admins may view all; editing allowed for IT Admin and District Admin in this phase

### Endpoints

#### `GET /api/interventions`

Supports query params:

- `student_id`
- `class_id`
- `status`

Returns interventions within caller scope, newest active-first.

#### `POST /api/interventions`

Creates a student or class intervention after validating one-target-only behavior and caller scope.

#### `PATCH /api/interventions/{intervention_id}`

Allows status changes, description updates, and outcome notes updates.

Target identity is immutable after creation.

---

## Frontend

### New files

| File | Responsibility |
|------|---------------|
| `src/components/interventions/InterventionList.tsx` | Shared active/resolved intervention list |
| `src/components/interventions/InterventionForm.tsx` | Shared create/edit form |
| `src/components/interventions/InterventionStatusBadge.tsx` | Visual status badge |

### Modified files

| File | Change |
|------|--------|
| `src/app/(protected)/students/[id]/page.tsx` | Add student intervention section |
| `src/components/dashboard/TeacherDashboard.tsx` | Add class intervention affordance |
| `src/components/dashboard/PrincipalDashboard.tsx` | Add class intervention affordance |
| `src/lib/types.ts` | Add intervention interfaces |

### UX

Student view:

- show interventions below score history
- allow create/update in-place for authorized roles
- separate active and resolved sections

Class contexts:

- allow a class intervention panel from class summary areas
- show recent active interventions prominently

### Frontend permissions

- teachers create/update only for students in their classes and classes they teach
- principals create/update only within their school
- district/IT admins can view all; both may edit in this phase

---

## Testing

`app/tests/test_interventions.py` should cover:

- create student intervention
- create class intervention
- reject both-target and no-target payloads
- scope enforcement for teacher/principal/district/IT roles
- patch status and outcome notes
- list filtering by `student_id`, `class_id`, and `status`

Frontend verification should cover:

- create form validation
- active/resolved rendering
- edit status flow
- role-based visibility of action controls

---

## Out of Scope for Phase 3B

- district-wide intervention dashboards
- reminder scheduling
- intervention templates
- multi-step review workflows
- intervention attachments or documents

---

## Implementation Tasks

- [x] **Task 1: Intervention model and schemas** — expand `app/models/intervention.py`; add `app/schemas/intervention.py`
- [x] **Task 2: Intervention routes and tests** — add `app/routes/interventions.py`, register router, implement `app/tests/test_interventions.py`
- [x] **Task 3: Frontend intervention types and shared components** — extend `src/lib/types.ts`; add intervention UI components
- [ ] **Task 4: Student intervention workflow** — update `src/app/(protected)/students/[id]/page.tsx`
- [ ] **Task 5: Class intervention workflow** — update teacher/principal dashboard components

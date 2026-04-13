# Compass — Phase 2 Design Spec

**Date:** 2026-04-13
**Scope:** Phase 2 — Teacher, principal, and district dashboards with inline at-risk alerts
**Approach:** Option A (three role-specific backend endpoints) — each returns a fully assembled payload for its role

---

## Context

Phase 1 delivered: auth, all DB tables, student/score management, CSV import, admin CRUD, seed data.

Phase 2 adds dashboards and alerts. All tier logic already exists in `app/services/mtss.py`. Phase 2 builds on it without modification.

---

## Backend

### New files

| File | Responsibility |
|------|---------------|
| `app/schemas/dashboard.py` | Pydantic response models for all three dashboard payloads |
| `app/services/dashboard.py` | Aggregation functions: tier distribution, at-risk lists, class/school summaries |
| `app/routes/dashboard.py` | Three endpoints, each protected by `require_role` |
| `app/tests/test_dashboard.py` | Endpoint + service tests |

### Modified files

| File | Change |
|------|--------|
| `app/main.py` | Register `dashboard_router` |

### Endpoints

#### `GET /api/dashboard/teacher`
Roles: `teacher`, `it_admin`

Returns:
```json
{
  "classes": [
    {
      "id": "...",
      "name": "...",
      "grade_level": 1,
      "student_count": 12,
      "avg_score": 78.4,
      "tier_distribution": { "tier1": 6, "tier2": 4, "tier3": 2 }
    }
  ],
  "at_risk": [
    {
      "student_id": "...",
      "student_name": "...",
      "class_name": "...",
      "avg_score": 65.2,
      "tier": "tier3"
    }
  ]
}
```

#### `GET /api/dashboard/principal`
Roles: `principal`, `it_admin`, `district_admin`

Requires `school_id` query param for `it_admin` and `district_admin`. For `principal`, uses `current_user.school_id` (set at user creation). Returns 400 if no school can be resolved.

Returns:
```json
{
  "school_name": "...",
  "total_students": 120,
  "tier_distribution": { "tier1": 70, "tier2": 30, "tier3": 20 },
  "classes": [
    {
      "id": "...",
      "name": "...",
      "grade_level": 3,
      "student_count": 24,
      "avg_score": 81.0,
      "tier_distribution": { "tier1": 18, "tier2": 4, "tier3": 2 }
    }
  ],
  "grade_averages": [
    { "grade_level": 3, "avg_score": 81.0, "student_count": 24 }
  ],
  "at_risk": [
    {
      "student_id": "...",
      "student_name": "...",
      "class_name": "...",
      "avg_score": 65.2,
      "tier": "tier3"
    }
  ]
}
```

#### `GET /api/dashboard/district`
Roles: `district_admin`, `it_admin`

Returns:
```json
{
  "total_students": 400,
  "tier_distribution": { "tier1": 240, "tier2": 100, "tier3": 60 },
  "schools": [
    {
      "id": "...",
      "name": "...",
      "student_count": 200,
      "avg_score": 79.5,
      "tier_distribution": { "tier1": 120, "tier2": 50, "tier3": 30 },
      "high_risk": true
    }
  ]
}
```

`high_risk` is `true` when Tier 3 students exceed 30% of the school's total.

### Aggregation logic

`app/services/dashboard.py` contains:

- `get_class_summary(db, class_id)` → student count, avg score, tier counts (using `calculate_tier` from `mtss.py`)
- `get_at_risk_students(db, class_ids)` → flat list of Tier 2 + 3 students across given classes
- `get_grade_averages(db, school_id)` → avg score per grade level for a school
- `get_school_summary(db, school_id)` → aggregates class summaries into school-level counts

All functions take a `db: Session` argument. No global state.

---

## Frontend

### New files

| File | Responsibility |
|------|---------------|
| `src/app/(protected)/dashboard/page.tsx` | Role switch — calls right endpoint, renders right component |
| `src/components/dashboard/TeacherDashboard.tsx` | Class cards + at-risk table |
| `src/components/dashboard/PrincipalDashboard.tsx` | School summary + class table + at-risk table |
| `src/components/dashboard/DistrictDashboard.tsx` | Per-school table with tier distribution + high-risk flags |
| `src/components/dashboard/TierBadge.tsx` | Colored badge: Tier 1 = green, Tier 2 = yellow, Tier 3 = red |
| `src/components/dashboard/TierDonut.tsx` | Recharts PieChart showing T1/T2/T3 percentages |

### Modified files

| File | Change |
|------|--------|
| `src/components/layout/sidebar.tsx` | Add "Dashboard" as first nav link (all roles) |
| `src/lib/types.ts` | Add dashboard payload interfaces |

### Dashboard page routing

`/dashboard/page.tsx` checks `user.role`:
- `teacher` → calls `/api/dashboard/teacher`, renders `<TeacherDashboard>`
- `principal` → calls `/api/dashboard/principal`, renders `<PrincipalDashboard>`
- `district_admin` → calls `/api/dashboard/district`, renders `<DistrictDashboard>`
- `it_admin` → calls `/api/dashboard/district`, renders `<DistrictDashboard>`

### Alert panels

Each dashboard component includes an "At-Risk Students" section — a compact table with columns: Name (links to `/students/[id]`), Class/School, Avg Score, Tier. Tier 3 rows highlighted red, Tier 2 rows highlighted yellow. Shown only when at-risk list is non-empty; hidden otherwise.

### TierDonut

Recharts `PieChart` with three slices: Tier 1 (green `#22c55e`), Tier 2 (yellow `#eab308`), Tier 3 (red `#ef4444`). Shows counts and percentages in tooltip. Used on class cards (teacher/principal view) and school cards (district view).

### Color constants

Consistent across badge and donut:
- Tier 1: `#22c55e` (green-500)
- Tier 2: `#eab308` (yellow-500)
- Tier 3: `#ef4444` (red-500)

---

## Testing

`app/tests/test_dashboard.py` seeds:
- 2 schools, 1 district_admin, 1 principal (school 1), 1 teacher (school 1, class 1)
- 2 classes in school 1, 1 class in school 2
- Students with scores: some Tier 1, some Tier 2, some Tier 3 (using known averages across the tier boundaries)

Assertions:
- Teacher endpoint returns only their classes (not school 2 or unassigned classes)
- At-risk list contains only Tier 2 + 3 students
- Principal endpoint scoped to their school only
- District endpoint aggregates both schools
- Grade averages are computed correctly
- `high_risk` flag set correctly at 30% threshold
- Wrong role → 403 (teacher → `/principal`, principal → `/district`)

---

## Out of Scope for Phase 2

- Score trend charts over time (deferred to Phase 3)
- Benchmark-overridden tier thresholds on dashboards (benchmarks UI is Phase 3)
- Separate `/alerts` page (alerts are inline on each dashboard)
- District admin scoped to specific schools (all schools for now)

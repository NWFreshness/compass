# Compass — Phase 4 Design Spec

**Date:** 2026-04-14
**Scope:** Phase 4 — Reports, Audit Log, Visual Polish
**Approach:** Implement in three sections; test and push to GitHub after each

---

## Context

Phases 1–3 delivered: auth, student/score management, dashboards, AI recommendations, interventions, benchmark management.

Phase 4 completes the application with:
- Downloadable reports (CSV + PDF) for student, class, school, and district
- Audit log UI with role-scoped visibility
- Visual polish: score color coding, subject performance bars, loading/empty/error states

---

## Section 1: Reports

### Backend

**New files:**

| File | Responsibility |
|------|---------------|
| `app/schemas/reports.py` | Typed Pydantic models for assembled report data |
| `app/services/reports.py` | Data assembly: `build_student_report_data`, `build_class_report_data`, `build_school_report_data`, `build_district_report_data` |
| `app/routes/reports.py` | Four endpoints with `?format=csv\|pdf` query param |

**Modified files:**

| File | Change |
|------|--------|
| `app/main.py` | Register `reports_router` |

**PDF generation:** `fpdf2` (pure Python, no system dependencies, Windows Server safe)

**Endpoints:**

```
GET /api/reports/student/{student_id}?format=csv|pdf
GET /api/reports/class/{class_id}?format=csv|pdf
GET /api/reports/school/{school_id}?format=csv|pdf
GET /api/reports/district?format=csv|pdf
```

**Role scoping:**
- Student/class report: teacher (own class), principal (own school), district_admin/it_admin (all)
- School report: principal (own school), district_admin/it_admin (all)
- District report: district_admin/it_admin only

**Report contents:**
- *Student:* name, grade, class, subject averages with tier, intervention count, most recent AI recommendation summary
- *Class:* class info, per-student name + avg score + tier, tier distribution summary
- *School:* school name, per-class summary, grade averages, at-risk count
- *District:* all schools with tier distribution, high-risk flags

### Frontend

**New files:**

| File | Responsibility |
|------|---------------|
| `src/app/(protected)/reports/page.tsx` | Report picker: type + format selector + download button |

**Modified files:**

| File | Change |
|------|--------|
| `src/components/layout/sidebar.tsx` | Add "Reports" nav entry (all roles) |
| `src/app/(protected)/students/[id]/page.tsx` | Add "Export Report" dropdown (CSV / PDF) |

---

## Section 2: Audit Log

### Backend

**Migration:** Add nullable `school_id` column to `audit_log` (populated from acting user's `school_id` at log time)

**New files:**

| File | Responsibility |
|------|---------------|
| `app/services/audit.py` | `log_action(db, user_id, action, entity_type, entity_id, detail, school_id)` helper |
| `app/routes/audit.py` | `GET /api/audit` with pagination + filters |
| `app/schemas/audit.py` | `AuditLogEntry` response model |

**Modified files:**

| File | Change |
|------|--------|
| `app/main.py` | Register `audit_router` |
| `app/routes/auth.py` | Log login and logout events |
| `app/routes/students.py` | Log student create and update |
| `app/routes/scores.py` | Log score create and bulk import |
| `app/routes/interventions.py` | Log intervention create and update |
| `app/routes/admin.py` | Log user create and delete |
| `alembic/versions/` | New migration for `school_id` column |

**Endpoint:** `GET /api/audit?page=1&per_page=50&action=&entity_type=&date_from=&date_to=`

Role scoping:
- IT Admin: all entries
- District Admin: entries where `school_id = current_user.school_id`

### Frontend

**New files:**

| File | Responsibility |
|------|---------------|
| `src/app/(protected)/admin/audit/page.tsx` | Paginated audit log table with filter bar |

**Modified files:**

| File | Change |
|------|--------|
| `src/components/layout/sidebar.tsx` | Add "Audit Log" nav entry (IT Admin + District Admin) |
| `src/lib/types.ts` | Add `AuditLogEntry` interface |

**UI:** Table columns: timestamp, username, action, entity type, entity ID, detail. Filter bar: date range, action, entity type.

---

## Section 3: Visual Polish

**New components:**

| File | Responsibility |
|------|---------------|
| `src/components/students/SubjectBar.tsx` | Horizontal bar per subject showing avg score % with green/yellow/red color fill based on tier |

**Modified files:**

| File | Change |
|------|--------|
| `src/app/(protected)/students/[id]/page.tsx` | Add `SubjectBar` grid for subject performance; color-code score table cells |
| `src/app/(protected)/students/page.tsx` | Add MTSS tier column with `TierBadge`; skeleton loading state |
| `src/components/dashboard/TeacherDashboard.tsx` | Bolder at-risk row highlights; improved card styling |
| `src/components/dashboard/PrincipalDashboard.tsx` | Same dashboard improvements |
| `src/components/dashboard/DistrictDashboard.tsx` | Same dashboard improvements |
| All data-heavy pages | Skeleton loaders, empty state messages, consistent error display |

**Color constants (reuse existing from TierBadge/TierDonut):**
- Tier 1 / green: `#22c55e`
- Tier 2 / yellow: `#eab308`
- Tier 3 / red: `#ef4444`

**Score color coding rule:** same as MTSS thresholds — green ≥80, yellow 70–79, red <70

---

## Implementation Tasks

### Section 1: Reports
- [ ] **Task 1:** `app/schemas/reports.py` + `app/services/reports.py` data assembly
- [ ] **Task 2:** `app/routes/reports.py` endpoints + register in `app/main.py`; add `fpdf2` dependency
- [ ] **Task 3:** Frontend `/reports` page + sidebar nav + student profile export button

### Section 2: Audit Log
- [ ] **Task 4:** Alembic migration for `audit_log.school_id` + `app/services/audit.py` + `app/schemas/audit.py`
- [ ] **Task 5:** `app/routes/audit.py` + register router + wire `log_action` into auth/student/score/intervention/admin routes
- [ ] **Task 6:** Frontend `/admin/audit` page + sidebar nav + `AuditLogEntry` type

### Section 3: Visual Polish
- [ ] **Task 7:** `SubjectBar` component + student profile visual upgrade
- [ ] **Task 8:** Student list tier column + skeleton/empty/error states across all data-heavy pages
- [ ] **Task 9:** Dashboard visual improvements

---

## Out of Scope for Phase 4

- Scheduled/emailed reports
- Audit log export (CSV/PDF of audit log itself)
- School-specific benchmark overrides
- Bulk student import beyond CSV scores

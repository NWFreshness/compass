# Compass Phase 5 — Skyward ETL Design

## Goal

Nightly import of grade data from Skyward (the district's SIS) into Compass, with a conflict review UI for cases where Skyward's value differs from what Compass already has.

## Architecture

```
Skyward nightly export
        │
        ▼
  etl/input/          ←── SFTP client (WinSCP) drops CSV here, or manual copy
        │
        ▼
  etl/skyward_import.py   (Windows Task Scheduler, 2 AM daily)
        │
        ├── valid new rows ──────────► INSERT into scores
        │
        ├── conflicts ───────────────► INSERT into import_conflicts (status=pending)
        │
        └── summary ─────────────────► etl/logs/YYYY-MM-DD.log
                                        processed file → etl/archive/
```

Runs on the same Windows Server as Compass. No new infrastructure required.

## Tech Stack

- ETL script: Python (uv), direct SQLAlchemy DB access — no HTTP dependency
- Scheduling: Windows Task Scheduler
- SFTP (future): WinSCP scripted mode as a separate Task Scheduler job
- Conflict UI: Next.js + FastAPI, same patterns as existing admin pages

---

## Components

### 1. `backend/etl/config.py`

Centralised path and DB config:

```python
from pathlib import Path

INPUT_DIR   = Path("etl/input")
ARCHIVE_DIR = Path("etl/archive")
LOG_DIR     = Path("etl/logs")
DB_PATH     = Path("compass.db")
```

### 2. `backend/etl/column_map.py`

Edited by IT admin to match the district's actual Skyward export headers. No code change needed when columns differ between districts.

```python
# Map Skyward CSV column names → Compass field names
COLUMN_MAP = {
    "student_id":   "StudentID",
    "subject_name": "CourseTitle",
    "score_type":   "AssignmentType",
    "value":        "Score",
    "date":         "AssignmentDate",
    "notes":        "Comments",       # optional column
}

# Map Skyward grade type strings → Compass ScoreType enum values
SCORE_TYPE_MAP = {
    "homework":   "homework",
    "assignment": "homework",
    "quiz":       "quiz",
    "test":       "test",
    "exam":       "test",
}
```

### 3. `backend/etl/skyward_import.py`

Main ETL script. Invoked as `uv run python etl/skyward_import.py`.

**Flow:**
1. Find the newest CSV in `INPUT_DIR` — log error and exit if none found
2. Open DB via SQLAlchemy (same engine as the Compass app)
3. For each row:
   - Look up student by `student_id_number`
   - Look up subject by name
   - Map score type via `SCORE_TYPE_MAP`
   - Validate value (0–100 float) and date (YYYY-MM-DD)
   - If any lookup fails or validation fails → log row error, skip row
   - If no existing score for student+subject+date+score_type → insert Score
   - If existing score with same value → skip silently
   - If existing score with different value → insert ImportConflict (status=pending)
4. Move processed CSV to `ARCHIVE_DIR/YYYY-MM-DD-<filename>`
5. Write summary to `LOG_DIR/YYYY-MM-DD.log`: total rows, inserted, skipped, conflicted, row errors

### 4. `backend/app/models/import_conflict.py`

```
import_conflicts table:
  id               UUID PK
  student_id       FK → students (cascade delete)
  subject_id       FK → subjects
  date             DATE
  score_type       homework | quiz | test
  compass_value    FLOAT
  skyward_value    FLOAT
  import_run_date  DATE
  status           pending | accepted | rejected
  resolved_by      FK → users (nullable)
  resolved_at      DATETIME (nullable)
```

### 5. `backend/app/routes/etl.py`

Three endpoints, all restricted to `it_admin`:

- `GET /api/etl/conflicts?status=pending&page=1&per_page=50` → paginated list
- `GET /api/etl/conflicts/count?status=pending` → `{ "count": N }` (for sidebar badge)
- `POST /api/etl/conflicts/{id}/resolve` → body `{ "action": "accept" | "reject" }`
  - `accept`: updates the matching Score row to `skyward_value`, marks conflict resolved
  - `reject`: marks conflict resolved, Score unchanged

### 6. Frontend — `/admin/conflicts` page

- Visible in sidebar for `it_admin` only, with a count badge when pending conflicts exist
- Table columns: Student, Subject, Date, Type, Compass Value, Skyward Value, Accept / Reject buttons
- "Resolved" tab showing history (accepted/rejected) with timestamps
- Sidebar fetches `/api/etl/conflicts/count?status=pending` on load to populate badge

---

## Data Flow Detail

### Happy path (new score)
Skyward row for Alice / Math / 2026-04-15 / quiz / 88 → no existing score → inserted directly.

### Duplicate, same value
Skyward row matches existing Compass score exactly → skipped silently, logged as "skipped".

### Conflict (value differs)
Existing Compass score: Alice / Math / 2026-04-15 / quiz / 72.
Skyward says: 68.
→ ImportConflict created: compass_value=72, skyward_value=68, status=pending.
IT admin sees it in the UI, decides which is correct.

### Invalid row
Unknown student ID, unknown subject, or unparseable value/date → logged as row error, skipped. No DB write.

---

## Error Handling

- If no input file found: log and exit cleanly (Task Scheduler marks job as failed, IT can check logs)
- Row-level errors: logged with row number and reason, do not abort the whole run
- DB errors: logged, run aborted, input file left in place for retry
- All errors are in the daily log file; no email alerting in scope for Phase 5

---

## Configuration & Scheduling

**Task Scheduler job (IT admin sets up once):**
- Program: `C:\path\to\backend\.venv\Scripts\python.exe`
- Arguments: `etl\skyward_import.py`
- Start in: `C:\path\to\backend`
- Trigger: daily at 2:00 AM
- Run whether user is logged on or not

**SFTP (when district provides access):**
A separate Task Scheduler job at 1:45 AM runs WinSCP in scripted mode to pull the latest Skyward export into `etl/input/`. The import script has no knowledge of SFTP — it only reads from the input folder.

---

## Testing

- Unit tests for `column_map` transform logic (row → Score fields)
- Unit tests for conflict detection (same value → skip, different value → conflict)
- Route tests for conflict list, count, and resolve endpoints
- Manual end-to-end test: drop a sample CSV into `etl/input/`, run the script, verify scores inserted and conflicts created

---

## Out of Scope (Phase 5)

- Email/notification when conflicts exist
- Skyward API integration (designed to be swappable into the extract step later)
- Bulk accept/reject all conflicts
- Student or subject auto-creation from Skyward data (students must already exist in Compass)

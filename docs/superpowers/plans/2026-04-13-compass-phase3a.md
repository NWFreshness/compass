# Compass Phase 3A Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Add benchmark-aware Ollama-powered student/class analysis with immutable recommendation history in the existing student and dashboard workflows.

**Architecture:** The backend owns all AI orchestration. FastAPI routes perform RBAC and delegate to an AI analysis service that builds deterministic student/class snapshots, calls a local Ollama client, stores immutable recommendation history rows, and returns structured responses. The frontend adds inline analyze/history UI on the student detail page and teacher/principal dashboard class views using shared AI components and existing API/auth patterns.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, httpx, pytest, Next.js, React, TypeScript, Tailwind CSS

---

### Task 1: AI Model and Schema Foundation

**Files:**
- Modify: `backend/app/models/ai_rec.py`
- Modify: `backend/alembic/versions/ccb6db26e00c_initial_schema.py`
- Create: `backend/app/schemas/ai.py`
- Test: `backend/app/tests/test_ai.py`

- [x] **Step 1: Write the failing schema/model test**

```python
import uuid
from datetime import datetime, timezone

from app.models import AIRec
from app.schemas.ai import AIRecommendationResponse


def test_ai_recommendation_response_serializes_snapshot_fields():
    rec = AIRec(
        id=uuid.uuid4(),
        target_type="student",
        student_id=uuid.uuid4(),
        class_id=None,
        created_by=uuid.uuid4(),
        model_name="llama3.2",
        temperature=0.7,
        prompt="prompt text",
        response="raw response",
        snapshot={
            "student": {"id": "s1", "name": "Ada"},
            "overall_average": 72.5,
            "recommended_tier": "tier2",
        },
        parse_error=None,
        created_at=datetime.now(timezone.utc),
    )

    payload = AIRecommendationResponse.model_validate(rec)

    assert payload.target_type == "student"
    assert payload.created_by == rec.created_by
    assert payload.model_name == "llama3.2"
    assert payload.snapshot["recommended_tier"] == "tier2"
```

- [x] **Step 2: Run test to verify it fails**

Run: `cmd /c "C:\External Drive\Compass\backend\.venv\Scripts\python.exe -m pytest backend\app\tests\test_ai.py -k schema -q"`

Expected: FAIL because `app.schemas.ai` and the new `AIRec` fields do not exist yet.

- [x] **Step 3: Add the model fields in `backend/app/models/ai_rec.py`**

```python
import enum
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Enum, Float, ForeignKey, JSON, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class AITargetType(str, enum.Enum):
    student = "student"
    class_ = "class"


class AIRec(Base):
    __tablename__ = "ai_recs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    target_type: Mapped[AITargetType] = mapped_column(Enum(AITargetType), nullable=False)
    student_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("students.id"), nullable=True)
    class_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("classes.id"), nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    temperature: Mapped[float] = mapped_column(Float, nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[str] = mapped_column(Text, nullable=False)
    snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    parse_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
```

- [x] **Step 4: Update the initial Alembic schema so migrated environments create the same `ai_recs` shape**

```python
op.create_table(
    "ai_recs",
    sa.Column("id", sa.Uuid(), nullable=False),
    sa.Column(
        "target_type",
        sa.Enum("student", "class", name="aitargettype", native_enum=False, create_constraint=True),
        nullable=False,
    ),
    sa.Column("student_id", sa.Uuid(), nullable=True),
    sa.Column("class_id", sa.Uuid(), nullable=True),
    sa.Column("created_by", sa.Uuid(), nullable=False),
    sa.Column("model_name", sa.String(length=100), nullable=False),
    sa.Column("temperature", sa.Float(), nullable=False),
    sa.Column("prompt", sa.Text(), nullable=False),
    sa.Column("response", sa.Text(), nullable=False),
    sa.Column("snapshot", sa.JSON(), nullable=False),
    sa.Column("parse_error", sa.Text(), nullable=True),
    sa.Column("created_at", sa.DateTime(), nullable=False),
    sa.CheckConstraint(
        "(target_type = 'student' AND student_id IS NOT NULL AND class_id IS NULL) OR "
        "(target_type = 'class' AND class_id IS NOT NULL AND student_id IS NULL)",
        name="ck_ai_recs_target_consistency",
    ),
    sa.ForeignKeyConstraint(["class_id"], ["classes.id"]),
    sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
    sa.ForeignKeyConstraint(["student_id"], ["students.id"]),
    sa.PrimaryKeyConstraint("id"),
)
```

- [x] **Step 5: Add the response schemas in `backend/app/schemas/ai.py`**

```python
import uuid
from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel


class AIRecommendationResponse(BaseModel):
    id: uuid.UUID
    target_type: Literal["student", "class"]
    student_id: Optional[uuid.UUID]
    class_id: Optional[uuid.UUID]
    created_by: uuid.UUID
    model_name: str
    temperature: float
    prompt: str
    response: str
    snapshot: dict[str, Any]
    parse_error: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
```

- [x] **Step 6: Expand the focused test coverage to catch the enum and invariant issues**

```python
def test_ai_recommendation_response_serializes_class_target(db):
    world = seed_ai_context(db)
    rec = AIRec(
        id=uuid.uuid4(),
        target_type=AITargetType.class_,
        student_id=None,
        class_id=world["class"].id,
        created_by=world["teacher"].id,
        model_name="llama3.2",
        temperature=0.7,
        prompt="prompt text",
        response="raw response",
        snapshot={"class": {"id": str(world["class"].id), "name": "5A"}, "recommended_tier": "tier2"},
        parse_error=None,
        created_at=datetime.now(timezone.utc),
    )

    payload = AIRecommendationResponse.model_validate(rec)

    assert payload.target_type == "class"
    assert payload.class_id == world["class"].id
    assert payload.created_by == world["teacher"].id


def test_ai_migration_declares_target_type_constraint():
    import pathlib

    migration_text = pathlib.Path(
        "backend/alembic/versions/ccb6db26e00c_initial_schema.py"
    ).read_text(encoding="utf-8")

    assert "create_constraint=True" in migration_text


def test_ai_recommendation_rejects_both_targets_populated(db):
    world = seed_ai_context(db)
    rec = AIRec(
        target_type=AITargetType.student,
        student_id=world["student"].id,
        class_id=world["class"].id,
        created_by=world["teacher"].id,
        model_name="llama3.2",
        temperature=0.7,
        prompt="prompt text",
        response="raw response",
        snapshot={},
        parse_error=None,
        created_at=datetime.now(timezone.utc),
    )

    with pytest.raises(IntegrityError):
        db.add(rec)
        db.flush()
```

- [x] **Step 7: Run test to verify it passes**

Run: `cmd /c "C:\External Drive\Compass\backend\.venv\Scripts\python.exe -m pytest backend\app\tests\test_ai.py -k schema -q"`

Expected: PASS

- [x] **Step 8: Commit**

```bash
git add backend/app/models/ai_rec.py backend/alembic/versions/ccb6db26e00c_initial_schema.py backend/app/schemas/ai.py backend/app/tests/test_ai.py
git commit -m "feat: add ai recommendation schemas"
```

### Task 2: Ollama Client and AI Analysis Service

**Files:**
- Modify: `backend/app/config.py`
- Create: `backend/app/services/ollama.py`
- Create: `backend/app/services/ai_analysis.py`
- Test: `backend/app/tests/test_ai.py`

- [x] **Step 1: Write the failing service tests**

```python
def test_build_student_snapshot_uses_benchmark_aware_tiers(db):
    world = seed_ai_world(db)

    snapshot = build_student_snapshot(db, world["student"].id)

    assert snapshot["student"]["name"] == "Ada Lovelace"
    assert snapshot["overall_average"] == 72.5
    assert snapshot["recommended_tier"] == "tier2"
    assert snapshot["subjects"][0]["tier"] in {"tier1", "tier2", "tier3"}


def test_parse_ai_response_extracts_structured_sections():
    text = """Recommended MTSS Tier: Tier 2
Curriculum Recommendations:
- reteach fractions
Intervention Strategies:
- small group work
Rationale:
Average score is 72.5 with low quiz performance."""

    parsed = parse_ai_response(text)

    assert parsed["recommended_tier"] == "tier2"
    assert parsed["curriculum_recommendations"] == ["reteach fractions"]
    assert parsed["intervention_strategies"] == ["small group work"]
```

- [x] **Step 2: Run test to verify it fails**

Run: `cmd /c "C:\External Drive\Compass\backend\.venv\Scripts\python.exe -m pytest backend\app\tests\test_ai.py -k \"snapshot or parse\" -q"`

Expected: FAIL because `build_student_snapshot` and `parse_ai_response` do not exist.

- [x] **Step 3: Add config fields in `backend/app/config.py`**

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "sqlite:///./compass.db"
    session_expiry_hours: int = 24
    cookie_secure: bool = False
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    ollama_temperature: float = 0.7
    ollama_timeout_seconds: float = 30.0
```

- [x] **Step 4: Add the Ollama client in `backend/app/services/ollama.py`**

```python
import httpx

from app.config import settings


class OllamaError(RuntimeError):
    pass


def generate_text(prompt: str) -> str:
    payload = {
        "model": settings.ollama_model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": settings.ollama_temperature},
    }
    try:
        response = httpx.post(
            f"{settings.ollama_url}/api/generate",
            json=payload,
            timeout=settings.ollama_timeout_seconds,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise OllamaError("Ollama request failed") from exc

    body = response.json()
    return body["response"]
```

- [x] **Step 5: Add snapshot/prompt/parse helpers in `backend/app/services/ai_analysis.py`**

```python
def parse_ai_response(text: str) -> dict:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return {
        "recommended_tier": next(
            (line.split(":", 1)[1].strip().lower().replace(" ", "") for line in lines if line.lower().startswith("recommended mtss tier:")),
            None,
        ),
        "curriculum_recommendations": [line[2:].strip() for line in lines if line.startswith("-")][:1],
        "intervention_strategies": [line[2:].strip() for line in lines if line.startswith("-")][1:2],
        "rationale": next((line for line in lines if line.lower().startswith("average score")), ""),
    }


def build_student_snapshot(db: Session, student_id: uuid.UUID) -> dict:
    student = db.query(Student).filter(Student.id == student_id).first()
    scores = (
        db.query(Score)
        .filter(Score.student_id == student_id)
        .order_by(Score.date.desc())
        .all()
    )
    overall_average = round(sum(score.value for score in scores) / len(scores), 1)
    subject_rows = []
    for subject_id in sorted({score.subject_id for score in scores}):
        subject_scores = [score for score in scores if score.subject_id == subject_id]
        avg = round(sum(score.value for score in subject_scores) / len(subject_scores), 1)
        subject_rows.append({
            "subject_id": str(subject_id),
            "average": avg,
            "tier": get_student_tier(db, student_id, subject_id).value,
        })
    return {
        "student": {"id": str(student.id), "name": student.name, "grade_level": student.grade_level},
        "overall_average": overall_average,
        "recommended_tier": calculate_tier(overall_average).value,
        "subjects": subject_rows,
        "recent_scores": [{"date": score.date.isoformat(), "value": score.value} for score in scores[:5]],
    }
```

- [x] **Step 6: Run the focused service tests**

Run: `cmd /c "C:\External Drive\Compass\backend\.venv\Scripts\python.exe -m pytest backend\app\tests\test_ai.py -k \"snapshot or parse\" -q"`

Expected: PASS

- [x] **Step 7: Commit**

```bash
git add backend/app/config.py backend/app/services/ollama.py backend/app/services/ai_analysis.py backend/app/tests/test_ai.py
git commit -m "feat: add ai analysis services"
```

### Task 3: AI Routes and Backend Test Coverage

**Files:**
- Create: `backend/app/routes/ai.py`
- Modify: `backend/app/main.py`
- Test: `backend/app/tests/test_ai.py`

- [x] **Step 1: Write the failing route tests**

```python
def test_student_ai_analysis_creates_history_entry(client, db, monkeypatch):
    world = seed_ai_world(db)
    monkeypatch.setattr("app.services.ollama.generate_text", lambda prompt: FAKE_AI_RESPONSE)

    assert client.post("/api/auth/login", json={"username": "teacher", "password": "password1"}).status_code == 200
    response = client.post(f"/api/ai/student/{world['student'].id}/analyze")

    assert response.status_code == 201
    payload = response.json()
    assert payload["target_type"] == "student"
    assert payload["snapshot"]["student"]["name"] == "Ada Lovelace"


def test_teacher_cannot_analyze_unassigned_class(client, db, monkeypatch):
    world = seed_ai_world(db)
    monkeypatch.setattr("app.services.ollama.generate_text", lambda prompt: FAKE_AI_RESPONSE)

    assert client.post("/api/auth/login", json={"username": "other_teacher", "password": "password1"}).status_code == 200
    response = client.post(f"/api/ai/class/{world['class'].id}/analyze")

    assert response.status_code == 403
```

- [x] **Step 2: Run test to verify it fails**

Run: `cmd /c "C:\External Drive\Compass\backend\.venv\Scripts\python.exe -m pytest backend\app\tests\test_ai.py -q"`

Expected: FAIL because `/api/ai/...` routes do not exist.

- [x] **Step 3: Add the routes in `backend/app/routes/ai.py`**

```python
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.middleware.auth import get_current_user
from app.models import Class, Student, User, UserRole
from app.schemas.ai import AIRecommendationResponse
from app.services.ai_analysis import analyze_class, analyze_student, list_class_history, list_student_history

router = APIRouter(prefix="/api/ai", tags=["ai"])


def _require_student_scope(db: Session, current_user: User, student_id: uuid.UUID) -> None:
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    if current_user.role == UserRole.teacher:
        class_ids = [row.id for row in db.query(Class).filter(Class.teacher_id == current_user.id).all()]
        if student.class_id not in class_ids:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
    if current_user.role == UserRole.principal and student.school_id != current_user.school_id:
        raise HTTPException(status_code=403, detail="Insufficient permissions")


@router.post("/student/{student_id}/analyze", response_model=AIRecommendationResponse, status_code=status.HTTP_201_CREATED)
def analyze_student_route(student_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _require_student_scope(db, current_user, student_id)
    return analyze_student(db, student_id=student_id, created_by=current_user.id)
```

- [x] **Step 4: Register the router in `backend/app/main.py`**

```python
from app.routes.ai import router as ai_router

app.include_router(ai_router)
```

- [x] **Step 5: Fill out history and class-analysis route coverage in `backend/app/tests/test_ai.py`**

```python
def test_student_history_is_newest_first(client, db):
    world = seed_ai_world(db)
    create_ai_rec(db, student_id=world["student"].id, created_at="2026-04-01T00:00:00+00:00")
    create_ai_rec(db, student_id=world["student"].id, created_at="2026-04-02T00:00:00+00:00")

    assert client.post("/api/auth/login", json={"username": "principal", "password": "password1"}).status_code == 200
    response = client.get(f"/api/ai/student/{world['student'].id}/history")

    assert response.status_code == 200
    assert response.json()[0]["created_at"] > response.json()[1]["created_at"]
```

- [x] **Step 6: Run the backend AI suite**

Run: `cmd /c "C:\External Drive\Compass\backend\.venv\Scripts\python.exe -m pytest backend\app\tests\test_ai.py -q"`

Expected: PASS

- [x] **Step 7: Commit**

```bash
git add backend/app/routes/ai.py backend/app/main.py backend/app/tests/test_ai.py
git commit -m "feat: add ai analysis routes"
```

### Task 4: Frontend AI Types and Shared Components

**Files:**
- Modify: `frontend/src/lib/types.ts`
- Create: `frontend/src/components/ai/AnalyzeButton.tsx`
- Create: `frontend/src/components/ai/AnalysisCard.tsx`
- Create: `frontend/src/components/ai/AnalysisHistory.tsx`
- Test: `frontend/src/app/(protected)/students/[id]/page.tsx` via lint/build

- [x] **Step 1: Add AI types to `frontend/src/lib/types.ts`**

```ts
export interface AIAnalysisSnapshot {
  overall_average: number;
  recommended_tier: "tier1" | "tier2" | "tier3";
  student?: { id: string; name: string; grade_level: number };
  class?: { id: string; name: string; grade_level: number };
  subjects: { subject_id: string; average: number; tier: "tier1" | "tier2" | "tier3" }[];
  recent_scores: { date: string; value: number }[];
}

export interface AIRecommendation {
  id: string;
  target_type: "student" | "class";
  student_id: string | null;
  class_id: string | null;
  model_name: string;
  temperature: number;
  response: string;
  snapshot: AIAnalysisSnapshot;
  parse_error: string | null;
  created_at: string;
}
```

- [x] **Step 2: Create `frontend/src/components/ai/AnalyzeButton.tsx`**

```tsx
"use client";

import { Button } from "@/components/ui/button";

export function AnalyzeButton({
  label,
  loading,
  onClick,
}: {
  label: string;
  loading: boolean;
  onClick: () => void;
}) {
  return (
    <Button onClick={onClick} disabled={loading}>
      {loading ? "Analyzing..." : label}
    </Button>
  );
}
```

- [x] **Step 3: Create `frontend/src/components/ai/AnalysisCard.tsx`**

```tsx
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { AIRecommendation } from "@/lib/types";

export function AnalysisCard({ recommendation }: { recommendation: AIRecommendation }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">Latest Recommendation</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 text-sm">
        <p><span className="font-medium">Recommended tier:</span> {recommendation.snapshot.recommended_tier}</p>
        <p><span className="font-medium">Model:</span> {recommendation.model_name}</p>
        <p className="whitespace-pre-wrap">{recommendation.response}</p>
      </CardContent>
    </Card>
  );
}
```

- [x] **Step 4: Create `frontend/src/components/ai/AnalysisHistory.tsx`**

```tsx
import type { AIRecommendation } from "@/lib/types";

export function AnalysisHistory({ items }: { items: AIRecommendation[] }) {
  if (items.length === 0) {
    return <p className="text-sm text-slate-500">No recommendation history yet.</p>;
  }

  return (
    <div className="space-y-3">
      {items.map((item) => (
        <div key={item.id} className="rounded-md border p-3 text-sm">
          <p className="font-medium">{new Date(item.created_at).toLocaleString()}</p>
          <p className="text-slate-500">Tier: {item.snapshot.recommended_tier}</p>
          <p className="mt-2 whitespace-pre-wrap">{item.response}</p>
        </div>
      ))}
    </div>
  );
}
```

- [x] **Step 5: Run frontend lint**

Run: `cmd /c npm.cmd run lint`

Workdir: `C:\External Drive\Compass\frontend`

Expected: PASS

- [x] **Step 6: Commit**

```bash
git add frontend/src/lib/types.ts frontend/src/components/ai/AnalyzeButton.tsx frontend/src/components/ai/AnalysisCard.tsx frontend/src/components/ai/AnalysisHistory.tsx
git commit -m "feat: add shared ai frontend components"
```

### Task 5: Student AI Workflow

**Files:**
- Modify: `frontend/src/app/(protected)/students/[id]/page.tsx`
- Modify: `frontend/src/lib/types.ts`
- Test: frontend lint/build

- [x] **Step 1: Write the student page state additions**

```tsx
const [history, setHistory] = useState<AIRecommendation[]>([]);
const [analyzing, setAnalyzing] = useState(false);

async function load() {
  const [studentData, scoreData, subjectData, aiHistory] = await Promise.all([
    api.get<Student>(`/students/${params.id}`),
    api.get<Score[]>(`/scores/student/${params.id}`),
    api.get<Subject[]>("/lookups/subjects"),
    api.get<AIRecommendation[]>(`/ai/student/${params.id}/history`),
  ]);
  setStudent(studentData);
  setScores(scoreData);
  setSubjects(subjectData);
  setHistory(aiHistory);
}

async function handleAnalyzeStudent() {
  setAnalyzing(true);
  setError("");
  try {
    const created = await api.post<AIRecommendation>(`/ai/student/${params.id}/analyze`);
    setHistory((current) => [created, ...current]);
  } catch (err: unknown) {
    setError(err instanceof Error ? err.message : "Unable to analyze student");
  } finally {
    setAnalyzing(false);
  }
}
```

- [x] **Step 2: Insert the AI UI in `frontend/src/app/(protected)/students/[id]/page.tsx`**

```tsx
<Card>
  <CardContent className="space-y-4 p-6">
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm font-medium">AI Recommendation</p>
        <p className="text-sm text-slate-500">Generate benchmark-aware support guidance for this student.</p>
      </div>
      <AnalyzeButton label="Analyze Student" loading={analyzing} onClick={() => void handleAnalyzeStudent()} />
    </div>
    {history[0] ? <AnalysisCard recommendation={history[0]} /> : null}
    <AnalysisHistory items={history} />
  </CardContent>
</Card>
```

- [x] **Step 3: Run frontend lint**

Run: `cmd /c npm.cmd run lint`

Workdir: `C:\External Drive\Compass\frontend`

Expected: PASS

- [x] **Step 4: Run frontend build**

Run: `cmd /c "set NEXT_DIST_DIR=.next-build-phase3a&& npm.cmd run build"`

Workdir: `C:\External Drive\Compass\frontend`

Expected: PASS with `/students/[id]` and existing routes compiled.

- [x] **Step 5: Commit**

```bash
git add frontend/src/app/(protected)/students/[id]/page.tsx frontend/src/lib/types.ts
git commit -m "feat: add student ai workflow"
```

### Task 6: Class AI Workflow in Dashboards

**Files:**
- Modify: `frontend/src/components/dashboard/TeacherDashboard.tsx`
- Modify: `frontend/src/components/dashboard/PrincipalDashboard.tsx`
- Modify: `frontend/src/lib/types.ts`
- Test: frontend lint/build

- [x] **Step 1: Add class analysis state to `TeacherDashboard.tsx`**

```tsx
const [classHistory, setClassHistory] = useState<Record<string, AIRecommendation[]>>({});
const [loadingClassId, setLoadingClassId] = useState<string | null>(null);

async function handleAnalyzeClass(classId: string) {
  setLoadingClassId(classId);
  try {
    const created = await api.post<AIRecommendation>(`/ai/class/${classId}/analyze`);
    setClassHistory((current) => ({
      ...current,
      [classId]: [created, ...(current[classId] ?? [])],
    }));
  } finally {
    setLoadingClassId(null);
  }
}
```

- [x] **Step 2: Add the class action UI in `TeacherDashboard.tsx`**

```tsx
<div className="flex items-center justify-between">
  <div>
    <CardTitle className="text-base">{cls.name}</CardTitle>
    <p className="text-sm text-slate-500">Grade {cls.grade_level}</p>
  </div>
  <AnalyzeButton
    label="Analyze Class"
    loading={loadingClassId === cls.id}
    onClick={() => void handleAnalyzeClass(cls.id)}
  />
</div>
{classHistory[cls.id]?.[0] ? <AnalysisCard recommendation={classHistory[cls.id][0]} /> : null}
```

- [x] **Step 3: Mirror the same class-analysis pattern in `PrincipalDashboard.tsx`**

```tsx
<TableCell className="text-right">
  <AnalyzeButton
    label="Analyze Class"
    loading={loadingClassId === cls.id}
    onClick={() => void handleAnalyzeClass(cls.id)}
  />
</TableCell>
```

- [x] **Step 4: Run frontend lint**

Run: `cmd /c npm.cmd run lint`

Workdir: `C:\External Drive\Compass\frontend`

Expected: PASS

- [x] **Step 5: Run frontend build**

Run: `cmd /c "set NEXT_DIST_DIR=.next-build-phase3a&& npm.cmd run build"`

Workdir: `C:\External Drive\Compass\frontend`

Expected: PASS with `/dashboard` compiled successfully.

- [x] **Step 6: Run backend AI test suite one more time**

Run: `cmd /c "C:\External Drive\Compass\backend\.venv\Scripts\python.exe -m pytest backend\app\tests\test_ai.py -q"`

Expected: PASS

- [x] **Step 7: Commit**

```bash
git add frontend/src/components/dashboard/TeacherDashboard.tsx frontend/src/components/dashboard/PrincipalDashboard.tsx frontend/src/lib/types.ts
git commit -m "feat: add class ai dashboard workflows"
```

### Task 7: Final Verification and Branch Finish

**Files:**
- Verify only

- [x] **Step 1: Run backend AI tests**

Run: `cmd /c "C:\External Drive\Compass\backend\.venv\Scripts\python.exe -m pytest backend\app\tests\test_ai.py -q"`

Expected: PASS

- [x] **Step 2: Run existing backend regression checks**

Run: `cmd /c "C:\External Drive\Compass\backend\.venv\Scripts\python.exe -m pytest backend\app\tests\test_mtss.py backend\app\tests\test_scores.py -q"`

Expected: PASS

- [x] **Step 3: Run frontend lint**

Run: `cmd /c npm.cmd run lint`

Workdir: `C:\External Drive\Compass\frontend`

Expected: PASS

- [x] **Step 4: Run frontend production build**

Run: `cmd /c "set NEXT_DIST_DIR=.next-build-phase3a-final&& npm.cmd run build"`

Workdir: `C:\External Drive\Compass\frontend`

Expected: PASS

- [x] **Step 5: Review git diff and commit anything remaining**

```bash
git status --short
git diff --stat
```

- [x] **Step 6: Commit final cleanup if needed**

```bash
git add backend/app frontend/src
git commit -m "chore: finalize phase 3a ai analysis"
```

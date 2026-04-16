# AI Response Streaming Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stream Ollama AI tokens to the frontend as they are generated instead of waiting for the full response.

**Architecture:** FastAPI `StreamingResponse` sends SSE (Server-Sent Events) JSON chunks as Ollama yields tokens. The backend accumulates tokens, saves the `AIRec` to DB after the stream ends, and emits a final `done` event with the record ID. The frontend reads the stream with the Fetch API and appends tokens to a state string for live rendering.

**Tech Stack:** FastAPI `StreamingResponse`, httpx streaming, `ReadableStream` (browser Fetch API), React state

---

## File Map

| File | Change |
|------|--------|
| `backend/app/services/ollama.py` | Add `generate_stream()` generator |
| `backend/app/services/ai_analysis.py` | Add `analyze_student_stream()` and `analyze_class_stream()` generators |
| `backend/app/routes/ai.py` | Add two new `/analyze/stream` POST endpoints |
| `backend/tests/__init__.py` | Create (empty) |
| `backend/tests/test_ai_stream.py` | Create — unit tests for stream functions |
| `frontend/src/lib/api.ts` | Add `postStream()` helper |
| `frontend/src/app/(protected)/students/[id]/page.tsx` | Replace `handleAnalyzeStudent` with streaming version; add streaming render |

---

## Task 1: Backend — `generate_stream` in `ollama.py`

**Files:**
- Modify: `backend/app/services/ollama.py`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/test_ai_stream.py`

- [ ] **Step 1: Create test file**

```python
# backend/tests/test_ai_stream.py
import json
from unittest.mock import MagicMock, patch

import pytest

from app.services.ollama import OllamaError, generate_stream


def _make_lines(*tokens: str, done_at: int = -1) -> list[bytes]:
    lines = []
    for i, token in enumerate(tokens):
        is_done = i == (len(tokens) + done_at if done_at < 0 else done_at)
        lines.append(json.dumps({"response": token, "done": is_done}).encode())
    return lines


def test_generate_stream_yields_tokens():
    mock_response = MagicMock()
    mock_response.iter_lines.return_value = _make_lines("Hello", " world", "!")
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)

    with patch("app.services.ollama.httpx.stream", return_value=mock_response):
        tokens = list(generate_stream("test prompt"))

    assert tokens == ["Hello", " world", "!"]


def test_generate_stream_raises_on_http_error():
    import httpx

    mock_response = MagicMock()
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "bad", request=MagicMock(), response=MagicMock()
    )

    with patch("app.services.ollama.httpx.stream", return_value=mock_response):
        with pytest.raises(OllamaError):
            list(generate_stream("test prompt"))
```

- [ ] **Step 2: Create `backend/tests/__init__.py`**

Empty file — just touch it:
```bash
touch backend/tests/__init__.py
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
cd backend && uv run pytest tests/test_ai_stream.py::test_generate_stream_yields_tokens -v
```

Expected: `FAILED` — `generate_stream` not yet defined.

- [ ] **Step 4: Add `generate_stream` to `ollama.py`**

Replace the entire file content:

```python
import json
from collections.abc import Iterator

import httpx

from app.config import settings


class OllamaError(RuntimeError):
    pass


def generate_text(prompt: str) -> str:
    """Call local Ollama and return the generated text."""
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

    return response.json()["response"]


def generate_stream(prompt: str) -> Iterator[str]:
    """Call local Ollama with streaming and yield each token."""
    payload = {
        "model": settings.ollama_model,
        "prompt": prompt,
        "stream": True,
        "options": {"temperature": settings.ollama_temperature},
    }
    try:
        with httpx.stream(
            "POST",
            f"{settings.ollama_url}/api/generate",
            json=payload,
            timeout=settings.ollama_timeout_seconds,
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                data = json.loads(line)
                yield data["response"]
                if data.get("done"):
                    break
    except httpx.HTTPError as exc:
        raise OllamaError("Ollama request failed") from exc
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd backend && uv run pytest tests/test_ai_stream.py -v
```

Expected: both tests `PASSED`.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/ollama.py backend/tests/__init__.py backend/tests/test_ai_stream.py
git commit -m "feat: add generate_stream to ollama service"
```

---

## Task 2: Backend — Streaming analysis functions in `ai_analysis.py`

**Files:**
- Modify: `backend/app/services/ai_analysis.py`
- Modify: `backend/tests/test_ai_stream.py`

- [ ] **Step 1: Add tests for `analyze_student_stream`**

Append to `backend/tests/test_ai_stream.py`:

```python
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from app.services.ai_analysis import analyze_student_stream


def _make_db_with_student():
    student = MagicMock()
    student.id = uuid.uuid4()
    student.name = "Test Student"
    student.grade_level = 5

    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = student
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
    db.query.return_value.filter.return_value.all.return_value = []
    return db, student


def test_analyze_student_stream_yields_tokens_then_done():
    db, student = _make_db_with_student()
    saved_rec = MagicMock()
    saved_rec.id = uuid.uuid4()
    db.refresh = lambda rec: setattr(rec, "id", saved_rec.id)

    tokens = ["Hello", " world"]

    with patch("app.services.ai_analysis.generate_stream", return_value=iter(tokens)):
        results = list(analyze_student_stream(db, student_id=student.id, created_by=uuid.uuid4()))

    # All tokens yielded before done sentinel
    assert results[:-1] == tokens
    # Last result is the done sentinel
    assert results[-1].startswith("\n__DONE__:")
    # DB record was saved
    db.add.assert_called_once()
    db.commit.assert_called_once()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && uv run pytest tests/test_ai_stream.py::test_analyze_student_stream_yields_tokens_then_done -v
```

Expected: `FAILED` — `analyze_student_stream` not yet defined.

- [ ] **Step 3: Add `analyze_student_stream` and `analyze_class_stream` to `ai_analysis.py`**

Add these imports at the top of `backend/app/services/ai_analysis.py` (after existing imports):

```python
from collections.abc import Iterator
from app.services import ollama as ollama_client  # already imported — no change needed
```

The `ollama_client` import already exists. Add only `Iterator` to the imports:

```python
from collections.abc import Iterator
```

Then add both functions at the end of `backend/app/services/ai_analysis.py`:

```python
def analyze_student_stream(
    db: Session, *, student_id: uuid.UUID, created_by: uuid.UUID
) -> Iterator[str]:
    """Yield Ollama tokens for a student analysis, then save AIRec and yield done sentinel."""
    snapshot = build_student_snapshot(db, student_id)
    prompt = _build_student_prompt(snapshot)
    full_response = ""
    for token in ollama_client.generate_stream(prompt):
        full_response += token
        yield token

    parsed = parse_ai_response(full_response)
    parse_error = None if parsed.get("recommended_tier") else "Could not parse structured response"
    rec = AIRec(
        target_type=AITargetType.student,
        student_id=student_id,
        class_id=None,
        created_by=created_by,
        model_name=settings.ollama_model,
        temperature=settings.ollama_temperature,
        prompt=prompt,
        response=full_response,
        snapshot=snapshot,
        parse_error=parse_error,
        created_at=datetime.now(timezone.utc),
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    yield f"\n__DONE__:{rec.id}"


def analyze_class_stream(
    db: Session, *, class_id: uuid.UUID, created_by: uuid.UUID
) -> Iterator[str]:
    """Yield Ollama tokens for a class analysis, then save AIRec and yield done sentinel."""
    snapshot = build_class_snapshot(db, class_id)
    prompt = _build_class_prompt(snapshot)
    full_response = ""
    for token in ollama_client.generate_stream(prompt):
        full_response += token
        yield token

    parsed = parse_ai_response(full_response)
    parse_error = None if parsed.get("recommended_tier") else "Could not parse structured response"
    rec = AIRec(
        target_type=AITargetType.class_,
        student_id=None,
        class_id=class_id,
        created_by=created_by,
        model_name=settings.ollama_model,
        temperature=settings.ollama_temperature,
        prompt=prompt,
        response=full_response,
        snapshot=snapshot,
        parse_error=parse_error,
        created_at=datetime.now(timezone.utc),
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    yield f"\n__DONE__:{rec.id}"
```

- [ ] **Step 4: Run all stream tests**

```bash
cd backend && uv run pytest tests/test_ai_stream.py -v
```

Expected: all tests `PASSED`.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/ai_analysis.py backend/tests/test_ai_stream.py
git commit -m "feat: add analyze_student_stream and analyze_class_stream"
```

---

## Task 3: Backend — Streaming routes in `routes/ai.py`

**Files:**
- Modify: `backend/app/routes/ai.py`

- [ ] **Step 1: Add streaming endpoints**

Add these imports at the top of `backend/app/routes/ai.py` (after existing imports):

```python
import json
from collections.abc import Iterator
from fastapi.responses import StreamingResponse
from app.services.ai_analysis import analyze_student_stream, analyze_class_stream
```

Add these two helper and two route functions at the end of `backend/app/routes/ai.py`:

```python
def _sse_stream(gen: Iterator[str]):
    """Wrap a token generator as SSE, encoding each payload as JSON."""
    try:
        for token in gen:
            yield f"data: {json.dumps(token)}\n\n"
    except Exception as exc:
        yield f"data: {json.dumps({'__error__': str(exc)})}\n\n"


@router.post("/student/{student_id}/analyze/stream")
def analyze_student_stream_route(
    student_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_student_scope(db, current_user, student_id)
    gen = analyze_student_stream(db, student_id=student_id, created_by=current_user.id)
    return StreamingResponse(_sse_stream(gen), media_type="text/event-stream")


@router.post("/class/{class_id}/analyze/stream")
def analyze_class_stream_route(
    class_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_class_scope(db, current_user, class_id)
    gen = analyze_class_stream(db, class_id=class_id, created_by=current_user.id)
    return StreamingResponse(_sse_stream(gen), media_type="text/event-stream")
```

Note: Each token (including the `\n__DONE__:<id>` sentinel) is JSON-encoded so newlines and special characters in Ollama output don't break SSE framing.

- [ ] **Step 2: Start the backend and verify the endpoints appear**

```bash
cd backend && uv run uvicorn app.main:app --reload
```

Visit `http://localhost:8000/docs` — confirm `/api/ai/student/{student_id}/analyze/stream` and `/api/ai/class/{class_id}/analyze/stream` are listed.

- [ ] **Step 3: Commit**

```bash
git add backend/app/routes/ai.py
git commit -m "feat: add SSE streaming endpoints for student and class analysis"
```

---

## Task 4: Frontend — `postStream` helper in `api.ts`

**Files:**
- Modify: `frontend/src/lib/api.ts`

- [ ] **Step 1: Add `postStream` to `api.ts`**

Add this function before the `export const api` block in `frontend/src/lib/api.ts`:

```typescript
async function postStream(
  path: string,
  onToken: (token: string) => void,
  onDone: (recId: string) => void,
  onError: (msg: string) => void,
): Promise<void> {
  let res: Response;
  try {
    res = await fetch(`/api${path}`, { method: "POST", credentials: "include" });
  } catch {
    onError("Network error");
    return;
  }
  if (!res.ok || !res.body) {
    onError(`HTTP ${res.status}`);
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";
    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const raw: string = JSON.parse(line.slice(6));
      if (raw.startsWith("\n__DONE__:")) {
        onDone(raw.slice("\n__DONE__:".length));
      } else if (typeof (JSON.parse(line.slice(6)) as Record<string, unknown>).__error__ === "string") {
        onError((JSON.parse(line.slice(6)) as Record<string, unknown>).__error__ as string);
      } else {
        onToken(raw);
      }
    }
  }
}
```

Wait — the JSON is parsed twice in the error branch. Simplify:

```typescript
async function postStream(
  path: string,
  onToken: (token: string) => void,
  onDone: (recId: string) => void,
  onError: (msg: string) => void,
): Promise<void> {
  let res: Response;
  try {
    res = await fetch(`/api${path}`, { method: "POST", credentials: "include" });
  } catch {
    onError("Network error");
    return;
  }
  if (!res.ok || !res.body) {
    onError(`HTTP ${res.status}`);
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";
    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const payload: unknown = JSON.parse(line.slice(6));
      if (typeof payload !== "string") {
        const err = (payload as Record<string, unknown>).__error__;
        if (typeof err === "string") onError(err);
        continue;
      }
      if (payload.startsWith("\n__DONE__:")) {
        onDone(payload.slice("\n__DONE__:".length));
      } else {
        onToken(payload);
      }
    }
  }
}
```

Add `postStream` to the exported `api` object:

```typescript
export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "POST", body: body !== undefined ? JSON.stringify(body) : undefined }),
  patch: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "PATCH", body: JSON.stringify(body) }),
  delete: (path: string) => request<void>(path, { method: "DELETE" }),
  upload: <T>(path: string, formData: FormData) =>
    request<T>(path, { method: "POST", body: formData, headers: {} }),
  postStream,
};
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/lib/api.ts
git commit -m "feat: add postStream helper to api client"
```

---

## Task 5: Frontend — Streaming in student detail page

**Files:**
- Modify: `frontend/src/app/(protected)/students/[id]/page.tsx`

- [ ] **Step 1: Add streaming state variables**

In `StudentDetailPage`, add two new state variables alongside the existing ones (after `const [analyzing, setAnalyzing] = useState(false);`):

```typescript
const [streamingText, setStreamingText] = useState("");
const [isStreaming, setIsStreaming] = useState(false);
```

- [ ] **Step 2: Replace `handleAnalyzeStudent` with streaming version**

Replace the existing `handleAnalyzeStudent` function:

```typescript
async function handleAnalyzeStudent() {
  setIsStreaming(true);
  setStreamingText("");
  setError("");
  await api.postStream(
    `/ai/student/${params.id}/analyze/stream`,
    (token) => setStreamingText((prev) => prev + token),
    async (recId) => {
      setIsStreaming(false);
      try {
        const updated = await api.get<AIRecommendation[]>(`/ai/student/${params.id}/history`);
        setHistory(updated);
        setStreamingText("");
      } catch {
        setError("Analysis saved but failed to refresh history");
      }
    },
    (msg) => {
      setIsStreaming(false);
      setStreamingText("");
      setError(msg || "Analysis failed");
    },
  );
}
```

Also remove the old `const [analyzing, setAnalyzing] = useState(false);` state and its references, replacing uses of `analyzing` with `isStreaming`.

The `AnalyzeButton` line becomes:

```tsx
<AnalyzeButton label="Analyze Student" loading={isStreaming} onClick={() => void handleAnalyzeStudent()} />
```

- [ ] **Step 3: Add streaming text render**

Replace the existing AI recommendation section:

```tsx
{isStreaming && streamingText ? (
  <Card>
    <CardHeader className="pb-2">
      <CardTitle className="text-base">Analyzing...</CardTitle>
    </CardHeader>
    <CardContent className="text-sm">
      <p className="whitespace-pre-wrap text-slate-700 dark:text-slate-300">{streamingText}</p>
    </CardContent>
  </Card>
) : history[0] ? (
  <AnalysisCard recommendation={history[0]} />
) : null}
```

Keep the history section below unchanged.

- [ ] **Step 4: Start dev server and test manually**

```bash
cd frontend && npm run dev
```

1. Navigate to any student detail page
2. Click "Analyze Student"
3. Verify text appears token by token while button shows "Analyzing..."
4. Verify once complete, the `AnalysisCard` replaces the streaming text with the saved recommendation
5. Verify history updates with the new entry

- [ ] **Step 5: Commit**

```bash
git add frontend/src/app/(protected)/students/[id]/page.tsx
git commit -m "feat: stream AI analysis output token by token on student detail page"
```

---

## Self-Review

**Spec coverage:**
- `generate_stream` in `ollama.py` — Task 1 ✓
- `analyze_student_stream` / `analyze_class_stream` — Task 2 ✓
- `/analyze/stream` endpoints (student + class) — Task 3 ✓
- Frontend `postStream` helper — Task 4 ✓
- Student page streaming state + render — Task 5 ✓
- Error handling (`__ERROR__` → `onError`) — Task 3 + Task 4 ✓
- DB save after stream + `__DONE__` sentinel — Task 2 ✓
- Existing endpoints unchanged — no modifications to existing routes ✓

**Class analysis frontend:** The class analyze endpoint is wired on the backend (Task 3) but there is no frontend page that currently triggers class analysis. This is intentional — the backend is ready for when class analysis is added to a frontend page.

**No placeholders found.**

**Type consistency:** `postStream` signature in Task 4 matches usage in Task 5. `analyze_student_stream` return type `Iterator[str]` matches `_sse_stream` parameter. `AIRecommendation[]` type matches existing usage in the page.

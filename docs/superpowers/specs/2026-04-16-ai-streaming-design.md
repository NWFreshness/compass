# AI Response Streaming — Design Spec

**Date:** 2026-04-16
**Status:** Approved

## Problem

AI analysis (student and class) blocks the UI until Ollama finishes generating the full response, then displays it all at once. This creates a blank, unresponsive experience during generation which can take 10–30+ seconds.

## Solution

Stream Ollama tokens to the frontend via Server-Sent Events (SSE) so text appears incrementally as it is generated. The complete response is saved to the database after streaming ends, and the frontend receives the saved record ID via a sentinel event.

## Backend

### `backend/app/services/ollama.py`

Add `generate_stream(prompt: str) -> Iterator[str]`:
- Calls `/api/generate` with `stream: True`
- Uses `httpx` streaming context (`response.iter_lines()`)
- Parses each NDJSON line, yields the `"response"` field string
- Raises `OllamaError` on HTTP failure

Existing `generate_text` is unchanged.

### `backend/app/services/ai_analysis.py`

Add two generator functions:

**`analyze_student_stream(db, student_id, created_by) -> Iterator[str]`**
1. Build snapshot + prompt (same logic as `analyze_student`)
2. Yield each token from `generate_stream(prompt)`
3. Accumulate full response text
4. Save `AIRec` to DB (same fields as today)
5. Yield sentinel: `\n__DONE__:<rec_id>`

**`analyze_class_stream(db, class_id, created_by) -> Iterator[str]`**  
Same pattern for class analysis.

Existing `analyze_student` and `analyze_class` are unchanged.

### `backend/app/routes/ai.py`

Add two new endpoints alongside existing ones:

```
POST /api/ai/student/{student_id}/analyze/stream
POST /api/ai/class/{class_id}/analyze/stream
```

Both:
- Apply same RBAC scope checks as existing endpoints
- Return `StreamingResponse(media_type="text/event-stream")`
- Wrap each token as `data: <token>\n\n`
- Final message: `data: __DONE__:<rec_id>\n\n`

Existing `/analyze` endpoints are unchanged (no breaking changes).

## Frontend

### Streaming state (in parent page components)

Pages that host an `AnalyzeButton` (student detail page, class/dashboard panels) add:
- `streamingText: string` — accumulates tokens during active stream
- `isStreaming: boolean` — true while fetch stream is open

### Fetch logic (replace JSON POST with stream consumer)

On button click:
1. Set `isStreaming = true`, clear `streamingText`
2. `fetch("/api/ai/.../analyze/stream", { method: "POST" })`
3. Read `response.body` as `ReadableStream`, decode with `TextDecoder`
4. For each chunk: check for `__DONE__:<id>` sentinel
   - If found: set `isStreaming = false`, trigger history refresh
   - Otherwise: append token to `streamingText`

### Rendering during stream

While `isStreaming` is true, render `streamingText` in a card with `whitespace-pre-wrap` in place of the `AnalysisCard`. A blinking cursor or spinner indicates the stream is active.

Once done, `AnalysisCard` renders the freshly fetched `AIRec` from history as usual.

### `AnalysisCard` — no changes needed

It continues to render completed `AIRec` objects from history.

## Data Flow

```
User clicks Analyze
  → frontend POST /api/ai/.../analyze/stream
  → backend builds prompt, calls Ollama stream=true
  → backend yields SSE token chunks → frontend appends to streamingText
  → Ollama done → backend saves AIRec to DB → yields __DONE__:<id>
  → frontend stops stream, refreshes history → AnalysisCard renders saved rec
```

## Error Handling

- If Ollama errors mid-stream: backend yields `data: __ERROR__:<message>\n\n` and closes
- Frontend on `__ERROR__`: show error state, clear streaming text
- Network failure: caught in fetch, show existing error UI

## Non-Goals

- No changes to existing non-streaming `/analyze` endpoints
- No WebSocket infrastructure
- No changes to how `AIRec` is stored or parsed

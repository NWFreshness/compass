# Compass

Student Learning Analytics and MTSS Recommendation System for local deployment.

## Requirements

- Python 3.11+
- `uv`
- Node.js 20+ and npm
- Ollama for later AI features

## Installation

### Backend

```bash
cd backend
cp .env.example .env
uv sync
uv run alembic upgrade head
uv run python -m app.seed
```

### Frontend

```bash
cd frontend
npm install
```

## Running

### Windows

```bat
deploy\start.bat
```

### Linux / macOS

```bash
./deploy/start.sh
```

Or run each service manually:

```bash
cd backend && uv run uvicorn app.main:app --reload
cd frontend && npm run dev
```

## Default Accounts

| Username | Password | Role |
|----------|----------|------|
| admin | changeme | IT Admin |
| district | changeme | District Admin |
| principal | changeme | Principal |
| teacher | changeme | Teacher |

Change these passwords after initial setup.

## Database Backup

```bash
cp backend/compass.db backend/compass.db.bak
```

## Ollama

Phase 1 does not require Ollama, but later phases expect a local instance on `http://localhost:11434`.

```bash
ollama pull llama3.2
```

## Tests

```bash
cd backend && uv run pytest -v
cd frontend && npm run lint
cd frontend && npm run build
```

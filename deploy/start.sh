#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "Starting Compass backend..."
cd "$ROOT/backend"
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

sleep 2

echo "Starting Compass frontend..."
cd "$ROOT/frontend"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "Compass is running."
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM
wait

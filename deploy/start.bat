@echo off
echo Starting Compass...

start "Compass Backend" cmd /k "cd /d %~dp0..\backend && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000"
timeout /t 3 /nobreak >nul
start "Compass Frontend" cmd /k "cd /d %~dp0..\frontend && npm.cmd run dev"

echo.
echo Compass is starting up.
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:3000
echo   API docs: http://localhost:8000/docs
echo.
echo Close the two terminal windows to stop Compass.

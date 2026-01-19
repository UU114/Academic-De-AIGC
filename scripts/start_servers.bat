@echo off
cd /d "%~dp0.."

echo === Starting DEAI Servers ===
echo.

echo [Backend] Starting on port 8000...
start "DEAI-Backend" cmd /k "cd /d %~dp0.. && venv\Scripts\activate && python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 3 /nobreak > nul

echo [Frontend] Starting...
start "DEAI-Frontend" cmd /k "cd /d %~dp0..\frontend && npm run dev"

echo.
echo === Servers starting in separate windows ===
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
echo.
pause

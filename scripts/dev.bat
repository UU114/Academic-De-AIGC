@echo off
REM AcademicGuard Development Server Startup Script
REM Windows batch script for starting both frontend and backend

echo ====================================
echo  AcademicGuard Development Server
echo ====================================

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

REM Start backend server
echo.
echo Starting backend server on http://127.0.0.1:8000
echo API Documentation: http://127.0.0.1:8000/docs
echo.

start "AcademicGuard Backend" cmd /c "venv\Scripts\python.exe -m uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload"

REM Wait for backend to start
timeout /t 3 /nobreak > nul

REM Start frontend development server
echo Starting frontend server on http://127.0.0.1:5173
echo.

cd frontend
start "AcademicGuard Frontend" cmd /c "npm run dev"

echo.
echo ====================================
echo  Servers started successfully!
echo  Backend:  http://127.0.0.1:8000
echo  Frontend: http://127.0.0.1:5173
echo ====================================
echo.
echo Press any key to stop all servers...
pause > nul

REM Kill servers
taskkill /FI "WINDOWTITLE eq AcademicGuard Backend" /F 2>nul
taskkill /FI "WINDOWTITLE eq AcademicGuard Frontend" /F 2>nul

echo Servers stopped.

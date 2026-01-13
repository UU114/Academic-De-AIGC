@echo off
REM AcademicGuard Development Server Startup Script
REM Windows batch script for starting both frontend and backend
REM AcademicGuard 开发服务器启动脚本

echo ====================================
echo  AcademicGuard Development Server
echo ====================================
echo.

set PORT=8000
set PID_FILE=.server.pid

REM Check if port is already in use
REM 检查端口是否已被占用
echo Checking port %PORT%...

for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%PORT%" ^| findstr "LISTENING" 2^>nul') do (
    echo.
    echo WARNING: Port %PORT% is already in use by PID %%a
    echo.
    choice /C YN /M "Do you want to kill the existing process and continue"
    if errorlevel 2 (
        echo Startup cancelled.
        exit /b 1
    )
    if errorlevel 1 (
        echo Killing process %%a...
        taskkill /F /PID %%a >nul 2>&1
        timeout /t 2 /nobreak >nul
    )
)

REM Check and remove stale PID file
REM 检查并删除过期的PID文件
if exist %PID_FILE% (
    set /p OLD_PID=<%PID_FILE%
    tasklist /FI "PID eq %OLD_PID%" 2>nul | find "%OLD_PID%" >nul
    if errorlevel 1 (
        echo Removing stale PID file...
        del %PID_FILE% 2>nul
    ) else (
        echo.
        echo WARNING: Another server instance is running (PID: %OLD_PID%)
        choice /C YN /M "Do you want to kill it and continue"
        if errorlevel 2 (
            echo Startup cancelled.
            exit /b 1
        )
        if errorlevel 1 (
            echo Killing process %OLD_PID%...
            taskkill /F /PID %OLD_PID% >nul 2>&1
            del %PID_FILE% 2>nul
            timeout /t 2 /nobreak >nul
        )
    )
)

REM Check if virtual environment exists
REM 检查虚拟环境是否存在
if not exist "venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

REM Start backend server
REM 启动后端服务器
echo.
echo Starting backend server on http://127.0.0.1:%PORT%
echo API Documentation: http://127.0.0.1:%PORT%/docs
echo.

start "AcademicGuard Backend" cmd /c "venv\Scripts\python.exe -m uvicorn src.main:app --host 127.0.0.1 --port %PORT% --reload"

REM Wait for backend to start
REM 等待后端启动
timeout /t 3 /nobreak > nul

REM Verify backend started successfully
REM 验证后端是否启动成功
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://127.0.0.1:%PORT%/health' -TimeoutSec 5 -UseBasicParsing; if ($response.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
if errorlevel 1 (
    echo WARNING: Backend may not have started properly. Check the backend window for errors.
) else (
    echo Backend server started successfully.
)

REM Start frontend development server
REM 启动前端开发服务器
echo.
echo Starting frontend server on http://127.0.0.1:5173
echo.

cd frontend
start "AcademicGuard Frontend" cmd /c "npm run dev"
cd ..

echo.
echo ====================================
echo  Servers started successfully!
echo  Backend:  http://127.0.0.1:%PORT%
echo  Frontend: http://127.0.0.1:5173
echo ====================================
echo.
echo Press any key to stop all servers...
pause > nul

REM Kill servers using stop script
REM 使用stop脚本终止服务器
echo.
echo Stopping servers...
call scripts\stop.bat

REM Also kill frontend
REM 同时终止前端
taskkill /FI "WINDOWTITLE eq AcademicGuard Frontend" /F 2>nul

echo.
echo All servers stopped.

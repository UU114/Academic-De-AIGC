@echo off
REM AcademicGuard Server Stop Script
REM Windows batch script for stopping the server
REM AcademicGuard 服务器停止脚本

echo ====================================
echo  AcademicGuard Server Stop
echo ====================================
echo.

set PID_FILE=.server.pid
set PORT=8000

REM Check if PID file exists
REM 检查PID文件是否存在
if exist %PID_FILE% (
    set /p PID=<%PID_FILE%
    echo Found PID file with PID: %PID%

    REM Try to kill the process
    REM 尝试终止进程
    tasklist /FI "PID eq %PID%" 2>nul | find "%PID%" >nul
    if %ERRORLEVEL% == 0 (
        echo Stopping server process %PID%...
        taskkill /F /PID %PID% >nul 2>&1
        if %ERRORLEVEL% == 0 (
            echo Server stopped successfully.
        ) else (
            echo Failed to stop server.
        )
    ) else (
        echo Process %PID% is not running.
    )

    REM Remove PID file
    REM 删除PID文件
    del %PID_FILE% 2>nul
    echo PID file removed.
) else (
    echo No PID file found.
)

REM Also check and kill any process on port 8000
REM 同时检查并终止8000端口上的任何进程
echo.
echo Checking port %PORT%...

for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%PORT%" ^| findstr "LISTENING"') do (
    echo Found process %%a on port %PORT%
    taskkill /F /PID %%a >nul 2>&1
    if %ERRORLEVEL% == 0 (
        echo Killed process %%a
    )
)

echo.
echo ====================================
echo  Server cleanup complete
echo ====================================

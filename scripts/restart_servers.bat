@echo off
cd /d "%~dp0"

echo === Restarting DEAI Servers ===
echo.

echo [Step 1] Stopping existing servers...
powershell -ExecutionPolicy Bypass -File "%~dp0stop_servers.ps1"

timeout /t 2 /nobreak > nul

echo.
echo [Step 2] Starting servers...
call "%~dp0start_servers.bat"

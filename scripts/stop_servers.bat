@echo off
cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File "%~dp0stop_servers.ps1"
pause

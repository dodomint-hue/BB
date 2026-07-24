@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_dashboard_server.ps1"
if errorlevel 1 pause

@echo off
setlocal
set "PY=C:\Users\user\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not exist "%PY%" set "PY=python"
pushd "%~dp0"
start "BBTECH Dashboard Server" "%PY%" "%~dp0dashboard_proxy_server.py" 8765
timeout /t 2 >nul
start "" "http://127.0.0.1:8765/BBtech_Dashboard_Auto_google_sheet_sync_fixed.html"
popd
endlocal

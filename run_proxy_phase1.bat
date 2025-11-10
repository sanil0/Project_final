@echo off
REM Start DDoS proxy and keep it running for Phase 1 testing

echo.
echo ========================================
echo Starting DDoS Proxy for Phase 1 Testing
echo ========================================
echo.

cd /d D:\project_warp

REM Start the proxy
D:\project_warp\.venv\Scripts\python.exe start_simple.py

REM Keep proxy running
pause

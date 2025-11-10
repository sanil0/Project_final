@echo off
REM Quick local test: Start webapp + proxy + monitoring
REM This script runs everything needed for local testing

echo.
echo ========================================================
echo   Starting Local DDoS Protection Demo
echo ========================================================
echo.

REM Check prerequisites
where docker >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker not found. Please install Docker first.
    exit /b 1
)

echo [STEP 1] Ensuring Docker image is built...
docker build -t ddos-protection:latest . >nul 2>&1
echo [OK] Docker image ready

echo.
echo [STEP 2] Creating necessary directories...
if not exist "logs" mkdir logs
if not exist "models" mkdir models
if not exist "grafana-dashboards" mkdir grafana-dashboards
echo [OK] Directories created

echo.
echo [STEP 3] Starting DDoS Proxy + Monitoring Stack...
docker-compose -f docker-compose.production.yml up -d >nul 2>&1
echo [OK] Services starting...

echo.
echo [STEP 4] Waiting for services to initialize (30 seconds)...
timeout /t 30 /nobreak

echo.
echo ========================================================
echo   LOCAL TEST SETUP COMPLETE!
echo ========================================================
echo.
echo NEXT: Start the webapp in another terminal:
echo   cd webapp
echo   python main.py
echo.
echo Then access:
echo   Proxy:     http://localhost:8080/
echo   Dashboard: http://localhost:8000/dashboard/login
echo   Prometheus: http://localhost:9090
echo   Grafana:   http://localhost:3000
echo.
echo Login: admin / changeme
echo.
echo Test with: wrk -t4 -c500 -d10s http://localhost:8080/
echo.
echo To stop: docker-compose -f docker-compose.production.yml down
echo ========================================================
echo.

pause

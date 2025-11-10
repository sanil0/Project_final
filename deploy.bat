@echo off
REM Quick deployment script for DDoS Protection Proxy (Windows)
REM Usage: deploy.bat [start|stop|restart|status|logs|build]

setlocal enabledelayedexpansion

set COMPOSE_FILE=docker-compose.production.yml
set ENV_FILE=.env

if "%1%"=="" (
    set COMMAND=start
) else (
    set COMMAND=%1%
)

echo.
echo ====================================================
echo   DDoS Protection Proxy - Deployment Tool
echo ====================================================
echo.

:check_prereq
echo Checking prerequisites...
where docker >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed
    exit /b 1
)

where docker-compose >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Compose is not installed
    exit /b 1
)

if not exist "%ENV_FILE%" (
    echo [ERROR] %ENV_FILE% not found
    echo Creating from .env.production template...
    copy .env.production "%ENV_FILE%"
    echo Please edit %ENV_FILE% with your settings
    exit /b 1
)

echo [OK] All prerequisites met
echo.

:main
if "%COMMAND%"=="start" goto start_services
if "%COMMAND%"=="stop" goto stop_services
if "%COMMAND%"=="restart" goto restart_services
if "%COMMAND%"=="status" goto show_status
if "%COMMAND%"=="logs" goto show_logs
if "%COMMAND%"=="build" goto build_image

echo Usage: %0% [start^|stop^|restart^|status^|logs^|build]
echo.
echo Commands:
echo   start    - Start all services (default)
echo   stop     - Stop all services
echo   restart  - Restart all services
echo   status   - Show service status and health
echo   logs     - Show live logs
echo   build    - Build Docker image
exit /b 1

:create_dirs
if not exist "logs" mkdir logs
if not exist "certs" mkdir certs
if not exist "models" mkdir models
if not exist "grafana-dashboards" mkdir grafana-dashboards
echo [OK] Directories created
echo.
goto:eof

:build_image
echo Building Docker image...
docker build -t ddos-protection:latest .
echo [OK] Image built successfully
echo.
goto:eof

:start_services
call:create_dirs
call:build_image
echo Starting services...
docker-compose -f "%COMPOSE_FILE%" --env-file "%ENV_FILE%" up -d
echo [OK] Services started
echo Waiting for services to be ready (30 seconds)...
timeout /t 30 /nobreak
call:show_access_info
goto:eof

:stop_services
echo Stopping services...
docker-compose -f "%COMPOSE_FILE%" down
echo [OK] Services stopped
echo.
goto:eof

:restart_services
call:stop_services
call:start_services
goto:eof

:show_status
echo Service Status:
echo.
docker-compose -f "%COMPOSE_FILE%" ps
echo.
echo Health Checks:
powershell -NoProfile -Command "try { (Invoke-WebRequest -Uri 'http://localhost:8080/health' -ErrorAction Stop).StatusCode | Out-Null; Write-Host '[OK] Proxy is healthy' -ForegroundColor Green } catch { Write-Host '[ERROR] Proxy health check failed' -ForegroundColor Red }"
powershell -NoProfile -Command "try { (Invoke-WebRequest -Uri 'http://localhost:9090/-/healthy' -ErrorAction Stop).StatusCode | Out-Null; Write-Host '[OK] Prometheus is healthy' -ForegroundColor Green } catch { Write-Host '[ERROR] Prometheus health check failed' -ForegroundColor Red }"
echo.
goto:eof

:show_logs
echo Showing logs (Ctrl+C to exit)...
docker-compose -f "%COMPOSE_FILE%" logs -f
goto:eof

:show_access_info
echo.
echo ====================================================
echo   Services are Ready to Use!
echo ====================================================
echo.
echo Access Points:
echo   Dashboard:     http://localhost:8000/dashboard/login
echo   Prometheus:    http://localhost:9090
echo   Grafana:       http://localhost:3000
echo   Proxy API:     http://localhost:8080
echo.
echo Credentials:
for /f "tokens=2 delims==" %%i in ('findstr "^DASHBOARD_USER=" %ENV_FILE%') do set "DASHBOARD_USER=%%i"
echo   Dashboard User:  %DASHBOARD_USER%
echo   Grafana User:    admin / admin123
echo.
echo Quick Test:
echo   Test proxy: curl http://localhost:8080/
echo   View logs:  deploy.bat logs
echo.
goto:eof

endlocal

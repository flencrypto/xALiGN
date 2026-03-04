@echo off
setlocal

cd /d "%~dp0.."

echo ============================================
echo  Starting aLiGN
echo ============================================
echo.

REM Ensure .env exists (copy from example on first run)
if not exist ".env" (
    echo Creating .env from .env.example ...
    copy ".env.example" ".env" > nul
)

REM Check that Docker is available
where docker >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Docker was not found in PATH.
    echo Please ensure Docker Desktop is installed and running, then try again.
    echo Download: https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)

REM Check that Docker daemon is responding
docker info >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Docker daemon is not running.
    echo Please start Docker Desktop and wait for it to fully initialise, then try again.
    pause
    exit /b 1
)

echo Starting services with Docker Compose ...
docker-compose up -d --build

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Failed to start aLiGN. Check the output above for details.
    pause
    exit /b 1
)

echo.
echo ============================================
echo  aLiGN is running!
echo   Frontend : http://localhost:3000
echo   API docs : http://localhost:8000/docs
echo ============================================
echo.

REM Wait a few seconds for the containers to bind their ports before
REM opening the browser, otherwise the page may not be reachable yet.
timeout /t 3 /nobreak > nul
start "" "http://localhost:3000"

endlocal

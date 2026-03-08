@echo off
setlocal enabledelayedexpansion

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
    echo.
    echo ❌ ERROR: Docker Desktop is not installed or not on PATH
    echo.
    echo aLiGN requires Docker Desktop to run. Please:
    echo.
    echo 1. Download Docker Desktop from: https://www.docker.com/products/docker-desktop/
    echo 2. Install it and restart your computer
    echo 3. Run this script again
    echo.
    echo For help, visit: https://docs.docker.com/desktop/install/windows/
    echo.
    pause
    exit /b 1
)

REM Check that Docker daemon is running
echo Checking Docker daemon...
docker info >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ Docker daemon is not running.
    echo.
    echo Starting Docker Desktop... (this may take a few moments)
    timeout /t 2 /nobreak > nul
    
    REM Try to start Docker via the installed path
    if exist "%ProgramFiles%\Docker\Docker\Docker.exe" (
        start "" "%ProgramFiles%\Docker\Docker\Docker.exe"
    ) else if exist "%ProgramFiles(x86)%\Docker\Docker\Docker.exe" (
        start "" "%ProgramFiles(x86)%\Docker\Docker\Docker.exe"
    )
    
    echo Please wait for Docker Desktop to fully start (1-2 minutes)...
    timeout /t 30 /nobreak > nul
    
    REM Retry once
    docker info >nul 2>&1
    if !ERRORLEVEL! NEQ 0 (
        echo.
        echo ❌ Still unable to connect to Docker. Please:
        echo.
        echo 1. Open Docker Desktop manually
        echo 2. Wait for the Docker icon in system tray to show it's running
        echo 3. Run this script again
        echo.
        pause
        exit /b 1
    )
)

echo ✓ Docker is ready
echo.
echo Building and starting aLiGN services...
echo (This may take several minutes on first run)
echo.

REM Run docker-compose with build
docker-compose up -d --build

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ ERROR: Failed to start aLiGN.
    echo.
    echo Check the error messages above or run:
    echo   docker-compose logs
    echo.
    pause
    exit /b 1
)

echo.
echo ✓ aLiGN is starting...
echo.
echo Waiting for services to be ready (may take 10-30 seconds)...

REM Wait for backend to be ready
set "RETRIES=0"
set "MAX_RETRIES=30"
:WAIT_LOOP
if %RETRIES% GEQ %MAX_RETRIES% (
    echo.
    echo ⚠ Timeout waiting for services. They may still be initializing.
    echo.
    echo You can:
    echo   • Wait a moment and refresh your browser
    echo   • Check status: docker-compose ps
    echo   • View logs: docker-compose logs backend
    echo.
    timeout /t 3 /nobreak > nul
    goto OPEN_BROWSER
)

curl -s http://localhost:8000/health > nul 2>&1
if %ERRORLEVEL% EQU 0 (
    goto SERVICES_READY
)

timeout /t 1 /nobreak > nul
set /a RETRIES=%RETRIES%+1
goto WAIT_LOOP

:SERVICES_READY
echo ✓ aLiGN is ready!
echo.

:OPEN_BROWSER
echo ============================================
echo  aLiGN is running!
echo   Dashboard   : http://localhost:3000
echo   API Docs    : http://localhost:8000/docs
echo ============================================
echo.

REM Open browser after a brief delay
timeout /t 2 /nobreak > nul
start "" "http://localhost:3000/dashboard"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ℹ Open your browser and navigate to: http://localhost:3000
    echo.
)

endlocal


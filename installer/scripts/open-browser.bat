@echo off
REM Open aLiGN dashboard in the default browser.
REM If services are not running, start.bat should be launched first.

cd /d "%~dp0.."

REM Check if services are running
docker-compose ps 2>nul | findstr "Up" >nul
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ⚠ aLiGN services are not running.
    echo.
    echo Please run: start.bat
    echo.
    pause
    exit /b 1
)

echo Opening aLiGN Dashboard...
echo   http://localhost:3000/dashboard
echo.

start "" "http://localhost:3000/dashboard"

timeout /t 2 /nobreak > nul


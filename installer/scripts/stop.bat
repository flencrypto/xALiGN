@echo off
setlocal

cd /d "%~dp0.."

echo ============================================
echo  Stopping aLiGN
echo ============================================
echo.

REM Check that Docker is available
where docker >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Docker was not found in PATH.
    echo Cannot stop services without Docker installed.
    pause
    exit /b 1
)

REM Try to stop the containers
echo Stopping services...
docker-compose down

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ⚠ Note: Docker may not be running, or there are no services to stop.
    echo.
    timeout /t 2 /nobreak > nul
    goto END
)

echo.
echo ✓ aLiGN services have been stopped.
echo   Database data is preserved.
echo   Run start.bat to restart.
echo.

:END
endlocal
pause


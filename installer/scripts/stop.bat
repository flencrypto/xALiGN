@echo off
setlocal

cd /d "%~dp0.."

echo ============================================
echo  Stopping aLiGN
echo ============================================
echo.

where docker >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Docker was not found in PATH.
    pause
    exit /b 1
)

docker-compose down

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Failed to stop aLiGN. Check the output above for details.
    pause
    exit /b 1
)

echo.
echo aLiGN has been stopped.
echo.

endlocal
pause

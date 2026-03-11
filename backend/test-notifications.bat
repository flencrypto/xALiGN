@echo off
REM Test Fallback Notification System
REM Run this to validate the notification system is working correctly

setlocal enabledelayedexpansion

cd /d "%~dp0"
set "PYTHONPATH=%CD%\..;%PYTHONPATH%"

echo ========================================================================
echo  aLiGN - Notification System Test
echo ========================================================================
echo.
echo This will test the fallback notification system that alerts you when
echo the daily briefing email is missing.
echo.
echo Tests include:
echo   - Environment configuration
echo   - Windows file paths
echo   - User settings
echo   - X/Twitter draft creation
echo   - Gmail draft creation
echo   - Gmail briefing fetch
echo   - Full fallback orchestration
echo.
echo ========================================================================
echo.
echo Press any key to start tests...
pause >nul
echo.

REM Check if Python is available
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not found
    pause
    exit /b 1
)

REM Run the test suite
python tests\check_notifications.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================================================
    echo  [OK] ALL TESTS PASSED
    echo ========================================================================
    echo.
    echo The notification system is ready for production use.
    echo.
    echo What happens when no briefing email is found:
    echo   1. System checks user permissions
    echo   2. Creates X/Twitter DM draft: "@TheMrFlen Daily DC briefing missing..."
    echo   3. Creates Gmail draft email with troubleshooting steps
    echo   4. Logs detailed warnings for visibility
    echo   5. Does NOT auto-send (drafts only, safe mode)
    echo.
    echo To enable auto-send (not recommended):
    echo   - Set full_autopilot=True in user settings
    echo   - Only use for critical production environments
    echo.
) else (
    echo.
    echo ========================================================================
    echo  [ERROR] SOME TESTS FAILED
    echo ========================================================================
    echo.
    echo Please review the errors above and fix before using in production.
    echo.
    echo Common issues:
    echo   - Gmail OAuth not configured - run setup-gmail-oauth.bat
    echo   - Missing .env variables - check backend\.env
    echo   - NOTIFICATION_EMAIL not set - add your email to .env
    echo.
    echo For detailed setup instructions, see:
    echo   docs\gmail-fallback-setup.md
    echo.
)

echo.
echo Press any key to exit...
pause >nul

endlocal

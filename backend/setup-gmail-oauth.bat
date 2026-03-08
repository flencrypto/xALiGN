@echo off
REM Gmail OAuth Setup Wizard for Windows Desktop Users
REM This script helps users generate Gmail OAuth tokens for aLiGN

setlocal enabledelayedexpansion

cd /d "%~dp0"
set "CLIENT_SECRET_PATH=%~dp0client_secret.json"
set "CLIENT_SECRET_FOUND="

echo ========================================================================
echo  aLiGN - Gmail OAuth Setup Wizard
echo ========================================================================
echo.
echo This wizard will help you set up Gmail OAuth for automatic briefing
echo email fetching. You'll need:
echo.
echo   1. A Google Cloud project with Gmail API enabled
echo   2. OAuth 2.0 credentials (Desktop app type)
echo   3. The client_secret.json file downloaded from Google Cloud Console
echo.
echo ========================================================================
echo.

REM Check if Python is available
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not on PATH
    echo.
    echo aLiGN requires Python 3.11+ for backend services.
    echo.
    echo Please install Python from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo [OK] Python found
python --version
echo.

REM Check if client_secret.json exists (robust checks for script dir and cwd)
if exist "%~dp0client_secret.json" set "CLIENT_SECRET_FOUND=%~dp0client_secret.json"
if not defined CLIENT_SECRET_FOUND if exist ".\client_secret.json" set "CLIENT_SECRET_FOUND=%CD%\client_secret.json"
if not defined CLIENT_SECRET_FOUND if exist "%CD%\client_secret.json" set "CLIENT_SECRET_FOUND=%CD%\client_secret.json"

if not defined CLIENT_SECRET_FOUND (
    echo.
    echo [WARN] client_secret.json not found
    echo Current directory: %CD%
    echo Searched path: %CLIENT_SECRET_PATH%
    echo.
    echo Nearby matching files:
    dir /b "%~dp0client_secret*" 2>nul
    echo.
    echo SETUP INSTRUCTIONS:
    echo ========================================================================
    echo.
    echo 1. Open: https://console.cloud.google.com/apis/credentials
    echo 2. Create a new project (e.g., "align-gmail-fetch")
    echo 3. Click "Enable APIs and Services"
    echo 4. Search for "Gmail API" and enable it
    echo 5. Click "Create Credentials" then "OAuth 2.0 Client ID"
    echo 6. Choose "Desktop app" as the application type
    echo 7. Download the JSON file
    echo 8. Rename it to: client_secret.json
    echo 9. Copy it to this directory: %CD%
    echo 10. Run this script again
    echo.
    echo ========================================================================
    echo.
    pause
    exit /b 1
)

echo [OK] client_secret.json found at: %CLIENT_SECRET_FOUND%
echo.

REM Check if required Python packages are installed
echo Checking required Python packages...
python -c "import google_auth_oauthlib.flow" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [WARN] Required Python packages not installed
    echo.
    echo Installing Google Auth packages...
    pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
    echo.
)

echo [OK] Required packages installed
echo.

REM Run the OAuth token generator
echo ========================================================================
echo  Launching OAuth Token Generator
echo ========================================================================
echo.
echo A browser window will open shortly.
echo.
echo Please:
echo   1. Log in with the Gmail account that receives briefing emails
echo   2. Grant access to Gmail (read and modify permissions)
echo   3. Wait for the confirmation message
echo.
echo Press any key to continue...
pause >nul
echo.

python scripts\generate_gmail_token.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================================================
    echo  OAuth Setup Complete!
    echo ========================================================================
    echo.
    echo The credentials have been saved to token.pickle
    echo.
    echo NEXT STEPS:
    echo   1. Copy the GOOGLE_* environment variables printed above
    echo   2. Open the .env file (in the aLiGN installation directory)
    echo   3. Paste the variables into .env
    echo   4. Add your notification email:
    echo      NOTIFICATION_EMAIL=your-email@example.com
    echo   5. Save the .env file
    echo   6. Restart aLiGN services (stop.bat then start.bat)
    echo.
    echo ========================================================================
    echo.
    echo [SECURITY REMINDER]
    echo   • Keep client_secret.json and token.pickle secure
    echo   • Never share these files
    echo   • These files are already excluded from git (.gitignore)
    echo.
    echo Press any key to exit...
    pause >nul
) else (
    echo.
    echo [ERROR] OAuth setup failed
    echo.
    echo Common issues:
    echo   • Browser didn't open - try a different browser
    echo   • Access denied - make sure you clicked "Allow"
    echo   • Invalid client secret - re-download from Google Cloud Console
    echo.
    echo For help, see: docs\gmail-fallback-setup.md
    echo.
    pause
    exit /b 1
)

endlocal

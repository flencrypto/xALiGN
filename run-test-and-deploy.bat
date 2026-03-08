@echo off
setlocal enabledelayedexpansion

REM One-click local test + installer build for Windows.
set "ROOT_DIR=%~dp0"
set "BACKEND_DIR=%ROOT_DIR%backend"
set "INSTALLER_SCRIPT=%ROOT_DIR%installer\setup.iss"
set "PF64=%ProgramFiles%"
set "PF32=%ProgramFiles(x86)%"
set "ISCC_EXE=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist "!ISCC_EXE!" set "ISCC_EXE=!PF64!\Inno Setup 6\ISCC.exe"
if not exist "!ISCC_EXE!" set "ISCC_EXE=!PF32!\Inno Setup 6\ISCC.exe"
if not exist "!ISCC_EXE!" for %%I in (ISCC.exe) do set "ISCC_EXE=%%~$PATH:I"
set "OUT_EXE=%ROOT_DIR%installer\output\aLiGN-Setup.exe"

echo ================================================================
echo aLiGN Test and Deploy (Windows Installer Build)
echo ================================================================
echo.

if not exist "%BACKEND_DIR%\test-notifications.bat" (
  echo [ERROR] Missing test runner: %BACKEND_DIR%\test-notifications.bat
  exit /b 1
)

if not exist "%INSTALLER_SCRIPT%" (
  echo [ERROR] Missing installer script: %INSTALLER_SCRIPT%
  exit /b 1
)

if not exist "!ISCC_EXE!" (
  echo [ERROR] Inno Setup compiler not found at:
  echo         !PF32!\Inno Setup 6\ISCC.exe
  echo         !PF64!\Inno Setup 6\ISCC.exe
  echo         !PF32!\Inno Setup 6\ISCC.exe
  echo         or available on PATH as ISCC.exe
  echo [HINT] Install Inno Setup 6 from https://jrsoftware.org/isdl.php
  exit /b 1
)

echo [1/2] Running notification tests...
pushd "%BACKEND_DIR%"
call test-notifications.bat
set "TEST_EXIT=%ERRORLEVEL%"
popd

if not "%TEST_EXIT%"=="0" (
  echo.
  echo [FAIL] Tests failed. Deployment aborted.
  exit /b %TEST_EXIT%
)

echo.
echo [2/2] Building installer...
"!ISCC_EXE!" "!INSTALLER_SCRIPT!"
set "BUILD_EXIT=%ERRORLEVEL%"

if not "%BUILD_EXIT%"=="0" (
  echo.
  echo [FAIL] Installer build failed with exit code %BUILD_EXIT%.
  exit /b %BUILD_EXIT%
)

echo.
if exist "%OUT_EXE%" (
  echo [SUCCESS] Deployment artifact ready:
  echo           %OUT_EXE%
  exit /b 0
)

echo [WARN] Build completed but expected output file not found:
echo        %OUT_EXE%
exit /b 2

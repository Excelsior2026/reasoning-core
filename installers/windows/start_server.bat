@echo off
REM Start Reasoning Core web server (Windows)

setlocal

set "INSTALL_DIR=%~dp0"

REM Find Python
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON=python
) else (
    where python3 >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        set PYTHON=python3
    ) else (
        echo ❌ Python not found. Please install Python 3.9 or later.
        echo    Download from: https://www.python.org/downloads/
        pause
        exit /b 1
    )
)

REM Verify reasoning-core is installed
%PYTHON% -c "import reasoning_core" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ⚠️  reasoning-core not found. Installing dependencies...
    if exist "%INSTALL_DIR%installers\windows\install_dependencies.ps1" (
        powershell.exe -ExecutionPolicy Bypass -File "%INSTALL_DIR%installers\windows\install_dependencies.ps1" -InstallDir "%INSTALL_DIR%"
    ) else (
        %PYTHON% -m pip install -e "%INSTALL_DIR%" || %PYTHON% -m pip install reasoning-core
    )
)

echo.
echo 🧠 Starting Reasoning Core Web Server...
echo.
echo 📍 API Server: http://localhost:8000
echo 🌐 Web UI: http://localhost:3000 (run in separate terminal: cd %INSTALL_DIR%web && npm run dev)
echo 📚 API Docs: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

REM Change to install directory
cd /d "%INSTALL_DIR%"

REM Start backend server
%PYTHON% -m reasoning_core.web.server

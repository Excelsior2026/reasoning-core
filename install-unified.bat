@echo off
REM Unified installer and launcher for Reasoning Core (Windows)

setlocal enabledelayedexpansion

echo.
echo 🧠 Reasoning Core - Unified Installer ^& Launcher
echo ==============================================
echo.

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Find Python
set PYTHON_CMD=
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=python
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo ✓ Python !PYTHON_VERSION! found
) else (
    where python3 >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        set PYTHON_CMD=python3
        for /f "tokens=2" %%i in ('python3 --version 2^>^&1') do set PYTHON_VERSION=%%i
        echo ✓ Python !PYTHON_VERSION! found
    ) else (
        echo ✗ Python 3.9+ not found. Please install Python first.
        echo   Download from: https://www.python.org/downloads/
        pause
        exit /b 1
    )
)

REM Check pip
echo Checking pip...
%PYTHON_CMD% -m pip --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ✗ pip not found. Please install pip first.
    pause
    exit /b 1
)
echo ✓ pip found

REM Check Node.js
set NODE_AVAILABLE=false
echo Checking Node.js...
where node >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    for /f %%i in ('node --version') do set NODE_VERSION=%%i
    echo ✓ Node.js !NODE_VERSION! found
    
    where npm >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        for /f %%i in ('npm --version') do set NPM_VERSION=%%i
        echo ✓ npm !NPM_VERSION! found
        set NODE_AVAILABLE=true
    ) else (
        echo ⚠ npm not found. Web UI will not be available.
    )
) else (
    echo ⚠ Node.js not found. Web UI will not be available.
    echo   Install Node.js from https://nodejs.org/ for full functionality
)

echo.
echo Installing/Updating dependencies...
echo.

REM Upgrade pip
%PYTHON_CMD% -m pip install --upgrade pip --quiet

REM Install Python dependencies
echo Installing Python packages...
%PYTHON_CMD% -m pip install -e . --quiet
%PYTHON_CMD% -m pip install -r requirements-web.txt --quiet

echo ✓ Python dependencies installed
echo.

REM Install Node.js dependencies
if "%NODE_AVAILABLE%"=="true" if exist "web" (
    echo Installing Node.js packages...
    cd web
    call npm install --silent
    cd ..
    echo ✓ Node.js dependencies installed
    echo.
)

echo ==============================================
echo Installation Complete! 🎉
echo ==============================================
echo.

REM Check if user wants to start server
if "%1"=="" (
    echo Starting Reasoning Core servers...
    echo.

    REM Start backend server
    echo 🚀 Starting API server on http://localhost:8000
    start "Reasoning Core - API Server" cmd /k "%PYTHON_CMD% -m reasoning_core.web.server"

    REM Wait a moment
    timeout /t 3 /nobreak >nul

    REM Start frontend if available
    if "%NODE_AVAILABLE%"=="true" if exist "web" (
        echo 🌐 Starting Web UI on http://localhost:3000
        cd web
        start "Reasoning Core - Web UI" cmd /k "npm run dev"
        cd ..
    )

    echo.
    echo ✅ Servers started!
    echo.
    echo 📍 Access points:
    echo    API Server: http://localhost:8000
    if "%NODE_AVAILABLE%"=="true" (
        echo    Web UI:     http://localhost:3000
    )
    echo    API Docs:   http://localhost:8000/docs
    echo.
    echo Check the windows that opened for server output.
    echo Close those windows to stop the servers.
    echo.
) else if "%1"=="--no-start" (
    echo To start the servers, run:
    echo   install-unified.bat
    echo.
    echo Or manually:
    echo   Terminal 1: %PYTHON_CMD% -m reasoning_core.web.server
    if "%NODE_AVAILABLE%"=="true" (
        echo   Terminal 2: cd web ^&^& npm run dev
    )
) else (
    echo Unknown option: %1
    echo Usage: install-unified.bat [--no-start]
)

pause

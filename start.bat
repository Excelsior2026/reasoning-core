@echo off
REM Quick start script for Reasoning Core (Windows)

setlocal

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo.
echo 🧠 Starting Reasoning Core...
echo.

REM Find Python
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=python
) else (
    where python3 >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        set PYTHON_CMD=python3
    ) else (
        echo ✗ Python not found. Run install-unified.bat first
        pause
        exit /b 1
    )
)

REM Check if reasoning-core is installed
%PYTHON_CMD% -c "import reasoning_core" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ⚠ reasoning-core not installed. Running installer...
    echo.
    call install-unified.bat
    exit /b %ERRORLEVEL%
)

REM Start backend server
echo 🚀 Starting API server on http://localhost:8000
start "Reasoning Core - API Server" cmd /k "%PYTHON_CMD% -m reasoning_core.web.server"

REM Wait a moment
timeout /t 3 /nobreak >nul

REM Start frontend if available
if exist "web\node_modules" (
    if exist "web" (
        where npm >nul 2>&1
        if %ERRORLEVEL% EQU 0 (
            echo 🌐 Starting Web UI on http://localhost:3000
            cd web
            start "Reasoning Core - Web UI" cmd /k "npm run dev"
            cd ..
        )
    )
)

echo.
echo ✅ Servers started!
echo.
echo 📍 Access points:
echo    API Server: http://localhost:8000
if exist "web\node_modules" (
    echo    Web UI:     http://localhost:3000
)
echo    API Docs:   http://localhost:8000/docs
echo.
echo Check the windows that opened for server output.
echo Close those windows to stop the servers.
echo.
pause

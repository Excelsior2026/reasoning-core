@echo off
REM Start Reasoning Core web server (Windows)

setlocal

set "INSTALL_DIR=%~dp0"
set "PYTHONPATH=%INSTALL_DIR%lib\python;%PYTHONPATH%"

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
        pause
        exit /b 1
    )
)

echo.
echo 🧠 Starting Reasoning Core Web Server...
echo.
echo 📍 API Server: http://localhost:8000
echo 🌐 Web UI: http://localhost:3000
echo 📚 API Docs: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start backend server
cd /d "%INSTALL_DIR%"
start "Reasoning Core Backend" cmd /c "%PYTHON% -m reasoning_core.web.server"

REM Wait a moment
timeout /t 3 /nobreak >nul

REM Start frontend if it exists
if exist "%INSTALL_DIR%web\node_modules" (
    if exist "%INSTALL_DIR%web" (
        cd /d "%INSTALL_DIR%web"
        where npm >nul 2>&1
        if %ERRORLEVEL% EQU 0 (
            echo Starting frontend...
            start "Reasoning Core Frontend" cmd /c "npm run dev"
        )
    )
)

echo.
echo Servers started! Check the windows that opened.
echo.
pause

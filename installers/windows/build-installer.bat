@echo off
REM Build Windows installer using Inno Setup

setlocal

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%..\.."
set "BUILD_DIR=%SCRIPT_DIR%build"

echo 📦 Building Windows installer package...
echo.

REM Check for Inno Setup Compiler
set "INNO_SETUP=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist "%INNO_SETUP%" (
    set "INNO_SETUP=C:\Program Files\Inno Setup 6\ISCC.exe"
)

if not exist "%INNO_SETUP%" (
    echo ❌ Inno Setup Compiler not found!
    echo.
    echo Please download and install Inno Setup 6 from:
    echo https://jrsoftware.org/isdl.php
    echo.
    echo After installation, run this script again.
    pause
    exit /b 1
)

echo ✓ Found Inno Setup: %INNO_SETUP%
echo.

REM Clean previous build
if exist "%BUILD_DIR%" (
    echo Cleaning previous build...
    rmdir /s /q "%BUILD_DIR%"
)

mkdir "%BUILD_DIR%"

REM Compile installer
echo Compiling installer...
"%INNO_SETUP%" "%SCRIPT_DIR%installer.iss"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ Installer created successfully!
    echo 📦 Location: %BUILD_DIR%\ReasoningCore-0.1.0-windows-setup.exe
    echo.
    echo To test the installer:
    echo   "%BUILD_DIR%\ReasoningCore-0.1.0-windows-setup.exe"
) else (
    echo.
    echo ❌ Installer compilation failed!
    pause
    exit /b 1
)

pause

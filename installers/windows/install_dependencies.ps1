# Install dependencies for reasoning-core on Windows
# Run as Administrator

param(
    [string]$InstallDir = "C:\Program Files\ReasoningCore"
)

$ErrorActionPreference = "Stop"

Write-Host "🧠 Installing Reasoning Core Dependencies..." -ForegroundColor Cyan
Write-Host ""

# Check for admin privileges
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "⚠️  This script requires Administrator privileges." -ForegroundColor Yellow
    Write-Host "Please run PowerShell as Administrator and try again." -ForegroundColor Yellow
    exit 1
}

# Function to check if command exists
function Test-Command {
    param($Command)
    $null = Get-Command $Command -ErrorAction SilentlyContinue
    return $?
}

# Check for Python
$pythonInstalled = $false
$pythonPath = ""

if (Test-Command python) {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
    $pythonPath = (Get-Command python).Source
    $pythonInstalled = $true
}
elseif (Test-Command python3) {
    $pythonVersion = python3 --version 2>&1
    Write-Host "✓ Python 3 found: $pythonVersion" -ForegroundColor Green
    $pythonPath = (Get-Command python3).Source
    $pythonInstalled = $true
}

if (-not $pythonInstalled) {
    Write-Host "Python not found. Installing Python 3.11..." -ForegroundColor Yellow
    
    # Download Python installer
    $pythonUrl = "https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe"
    $pythonInstaller = "$env:TEMP\python-installer.exe"
    
    Write-Host "Downloading Python installer..." -ForegroundColor Yellow
    Invoke-WebRequest -Uri $pythonUrl -OutFile $pythonInstaller
    
    Write-Host "Installing Python (this may take a few minutes)..." -ForegroundColor Yellow
    Start-Process -FilePath $pythonInstaller -ArgumentList "/quiet", "InstallAllUsers=1", "PrependPath=1" -Wait
    
    # Refresh PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
    
    # Try to find Python again
    if (Test-Command python) {
        $pythonPath = (Get-Command python).Source
        Write-Host "✓ Python installed successfully" -ForegroundColor Green
    }
    else {
        Write-Host "❌ Python installation failed. Please install Python 3.9+ manually." -ForegroundColor Red
        exit 1
    }
}

# Install pip packages
Write-Host ""
Write-Host "📦 Installing Python dependencies..." -ForegroundColor Cyan

& $pythonPath -m pip install --upgrade pip setuptools wheel
& $pythonPath -m pip install --upgrade `
    pydantic>=2.0.0 `
    fastapi>=0.100.0 `
    "uvicorn[standard]>=0.23.0" `
    python-multipart>=0.0.6 `
    requests>=2.31.0 `
    beautifulsoup4>=4.12.0 `
    PyPDF2>=3.0.0 `
    python-docx>=1.0.0 `
    aiofiles>=23.0.0 `
    pyjwt>=2.8.0 `
    "python-jose[cryptography]>=3.3.0"

# Install reasoning-core itself if source exists
if (Test-Path (Join-Path $InstallDir "src")) {
    Write-Host "📦 Installing reasoning-core from source..." -ForegroundColor Cyan
    Push-Location $InstallDir
    & $pythonPath -m pip install -e .
    Pop-Location
} elseif (Test-Path (Join-Path $PSScriptRoot "..\..\src")) {
    Write-Host "📦 Installing reasoning-core from source..." -ForegroundColor Cyan
    $sourceDir = Join-Path $PSScriptRoot "..\.."
    & $pythonPath -m pip install -e $sourceDir
} else {
    Write-Host "📦 Installing reasoning-core from package..." -ForegroundColor Cyan
    & $pythonPath -m pip install reasoning-core
}

# Check for Node.js
if (Test-Command node) {
    $nodeVersion = node --version
    Write-Host "✓ Node.js found: $nodeVersion" -ForegroundColor Green
}
else {
    Write-Host "Node.js not found. Installing Node.js..." -ForegroundColor Yellow
    
    # Download Node.js installer
    $nodeUrl = "https://nodejs.org/dist/v20.10.0/node-v20.10.0-x64.msi"
    $nodeInstaller = "$env:TEMP\node-installer.msi"
    
    Write-Host "Downloading Node.js installer..." -ForegroundColor Yellow
    Invoke-WebRequest -Uri $nodeUrl -OutFile $nodeInstaller
    
    Write-Host "Installing Node.js (this may take a few minutes)..." -ForegroundColor Yellow
    Start-Process -FilePath msiexec.exe -ArgumentList "/i", $nodeInstaller, "/quiet", "/norestart" -Wait
    
    # Refresh PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
    
    if (Test-Command node) {
        Write-Host "✓ Node.js installed successfully" -ForegroundColor Green
    }
    else {
        Write-Host "⚠️  Node.js installation may require a restart. Continuing..." -ForegroundColor Yellow
    }
}

# Install npm packages
if (Test-Command npm) {
    Write-Host ""
    Write-Host "📦 Installing Node.js dependencies..." -ForegroundColor Cyan
    
    $webDir = Join-Path $InstallDir "web"
    if (Test-Path $webDir) {
        Push-Location $webDir
        npm install --production --legacy-peer-deps
        Pop-Location
    }
}

Write-Host ""
Write-Host "✅ All dependencies installed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Installation location: $InstallDir" -ForegroundColor Cyan
Write-Host ""
Write-Host "To start the server, run:" -ForegroundColor Cyan
Write-Host "  $InstallDir\start_server.bat" -ForegroundColor Yellow

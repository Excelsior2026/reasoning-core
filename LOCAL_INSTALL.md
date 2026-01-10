# Local Installation Guide

This guide explains how to install Reasoning Core locally on your machine.

## Quick Start (Recommended)

The easiest way to install and start Reasoning Core is to use the unified installer:

### macOS/Linux

```bash
./install-unified.sh
```

### Windows

```cmd
install-unified.bat
```

This unified installer will:
- ✅ Check for Python 3.9+ and pip
- ✅ Check for Node.js and npm (optional, for web UI)
- ✅ Install all Python dependencies
- ✅ Install all Node.js dependencies (if available)
- ✅ Set up the application
- ✅ **Automatically start the servers**

After running, you'll have:
- **API Server** running at http://localhost:8000
- **Web UI** running at http://localhost:3000 (if Node.js is installed)
- **API Docs** at http://localhost:8000/docs

To install without starting servers:
```bash
./install-unified.sh --no-start  # macOS/Linux
install-unified.bat --no-start    # Windows
```

## Quick Start Script (After Installation)

If you've already installed and just want to start the servers:

### macOS/Linux

```bash
./start.sh
```

### Windows

```cmd
start.bat
```

## Standard Installation (Without Auto-Start)

If you prefer to install dependencies without automatically starting the servers:

```bash
./install.sh
```

This script will:
- ✅ Check for Python 3.9+ and pip
- ✅ Check for Node.js and npm (optional, for web UI)
- ✅ Install all Python dependencies
- ✅ Install all Node.js dependencies (if available)
- ✅ Set up the application

## Manual Installation

If you prefer to install manually or the script doesn't work for your system:

### Prerequisites

1. **Python 3.9+** - [Download Python](https://www.python.org/downloads/)
2. **Node.js 18+** (optional, for web UI) - [Download Node.js](https://nodejs.org/)

### Step 1: Install Python Dependencies

```bash
# Install the package
pip install -e .

# Install web dependencies
pip install -r requirements-web.txt
```

### Step 2: Install Node.js Dependencies (for Web UI)

```bash
cd web
npm install
cd ..
```

### Step 3: Verify Installation

```bash
# Test Python installation
python -c "from reasoning_core import ReasoningAPI; print('✓ Python installation successful')"

# Test web server (if Node.js is installed)
cd web && npm run dev
```

## Starting the Application

### Option 1: Quick Start Script

**macOS/Linux:**
```bash
./start.sh
```

**Windows:**
```cmd
start.bat
```

This starts both the API server and Web UI automatically.

### Option 2: Using the Convenience Script

```bash
./run_web.sh
```

This starts the API server on `http://localhost:8000`.

### Option 3: Manual Start

**Terminal 1 - API Server:**
```bash
python -m reasoning_core.web.server
```

**Terminal 2 - Web UI (optional):**
```bash
cd web
npm run dev
```

## Access Points

Once running, you can access:

- **Web UI**: http://localhost:3000
- **API Server**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

## Platform-Specific Installers

For macOS and Windows, we provide installer packages that handle everything automatically:

### macOS

```bash
cd installers/macos
./build-pkg.sh
```

The installer will be created at: `installers/macos/build/ReasoningCore-0.1.0-macos.pkg`

### Windows

```batch
cd installers\windows
build-installer.bat
```

The installer will be created at: `installers/windows/build/ReasoningCore-0.1.0-windows-setup.exe`

See the [installers README](installers/README.md) for more details.

## Troubleshooting

### Python Not Found

If you get "Python not found":
- Make sure Python 3.9+ is installed
- Try `python3` instead of `python`
- Add Python to your PATH environment variable

### Node.js Not Found

If you get "Node.js not found":
- Install Node.js from https://nodejs.org/
- Or skip the web UI and use only the API server

### Port Already in Use

If port 8000 or 3000 is already in use:
- Stop the other application using the port
- Or modify the ports in:
  - API: `src/reasoning_core/web/server.py`
  - Web UI: `web/vite.config.js`

### Permission Errors

If you get permission errors:
- Use `pip install --user` instead of `pip install`
- Or use a virtual environment (recommended):

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -e .
pip install -r requirements-web.txt
```

## Virtual Environment (Recommended)

For a cleaner installation, use a virtual environment:

```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate     # Windows

# Install dependencies
pip install -e .
pip install -r requirements-web.txt

# Install Node.js dependencies
cd web && npm install && cd ..
```

## Verification

After installation, verify everything works:

```bash
# Test Python import
python -c "from reasoning_core import ReasoningAPI; print('✓ OK')"

# Test API server (in one terminal)
python -m reasoning_core.web.server

# Test web UI (in another terminal)
cd web && npm run dev
```

Then open http://localhost:3000 in your browser.

## Development Setup

For development, install additional dev dependencies:

```bash
pip install -e ".[dev]"
```

This installs:
- pytest (testing)
- black (code formatting)
- isort (import sorting)
- flake8 (linting)
- mypy (type checking)

## Next Steps

- Check out the [README](README.md) for usage examples
- Explore the [examples](examples/) directory
- Read the [API documentation](http://localhost:8000/docs) when the server is running

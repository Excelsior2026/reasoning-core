# Unified Installer Guide

The unified installer is a one-stop solution that installs all dependencies and starts the servers automatically.

## Overview

The unified installer (`install-unified.sh` for macOS/Linux, `install-unified.bat` for Windows) provides a complete installation and startup solution:

1. ✅ Checks for Python 3.9+ and pip
2. ✅ Checks for Node.js and npm (optional)
3. ✅ Installs all Python dependencies
4. ✅ Installs all Node.js dependencies (if available)
5. ✅ **Automatically starts the servers**

## Usage

### macOS/Linux

```bash
./install-unified.sh
```

### Windows

```cmd
install-unified.bat
```

### Install Without Starting Servers

If you want to install dependencies but not start the servers immediately:

**macOS/Linux:**
```bash
./install-unified.sh --no-start
```

**Windows:**
```cmd
install-unified.bat --no-start
```

## What Happens

### During Installation

1. **Dependency Checks**
   - Verifies Python 3.9+ is installed
   - Verifies pip is available
   - Checks for Node.js and npm (optional)

2. **Python Dependencies**
   - Upgrades pip to latest version
   - Installs reasoning-core in editable mode
   - Installs all web dependencies from `requirements-web.txt`

3. **Node.js Dependencies** (if Node.js is available)
   - Installs all npm packages from `web/package.json`
   - Sets up the frontend for development

4. **Auto-Start** (unless `--no-start` is used)
   - Starts the API server on port 8000
   - Starts the Web UI on port 3000 (if Node.js available)
   - Displays access URLs

### After Installation

The servers will be running and accessible at:

- **🌐 Web UI**: http://localhost:3000
- **🔌 API Server**: http://localhost:8000
- **📚 API Docs**: http://localhost:8000/docs

## Restarting Servers

After the initial installation, use the quick start scripts:

### macOS/Linux

```bash
./start.sh
```

### Windows

```cmd
start.bat
```

These scripts:
- Check if dependencies are installed
- Run the installer if needed
- Start the servers

## Comparison with Other Installers

| Feature | Unified Installer | Standard Installer | Platform Installer |
|---------|------------------|-------------------|-------------------|
| Install dependencies | ✅ | ✅ | ✅ |
| Auto-start servers | ✅ | ❌ | Optional |
| Cross-platform | ✅ | ✅ | Platform-specific |
| One command | ✅ | ✅ | Requires installer build |
| Best for | Quick start | Development | Distribution |

## Troubleshooting

### Installation Fails

1. **Check Python version**: Must be 3.9 or higher
   ```bash
   python3 --version
   ```

2. **Check pip**: Ensure pip is installed
   ```bash
   python3 -m pip --version
   ```

3. **Check permissions**: May need to use `sudo` on macOS/Linux
   ```bash
   sudo ./install-unified.sh
   ```

### Servers Don't Start

1. **Check ports**: Ensure ports 8000 and 3000 are available
2. **Check logs**: Look for error messages in terminal output
3. **Manual start**: Try starting manually:
   ```bash
   python3 -m reasoning_core.web.server
   cd web && npm run dev
   ```

### Node.js Not Found

The installer will work without Node.js, but the Web UI won't be available. To add Node.js:

**macOS:**
```bash
brew install node
```

**Windows:**
- Download from https://nodejs.org/

Then run the installer again to install Node.js dependencies.

## Advanced Usage

### Custom Installation Directory

The unified installer installs in the current directory. To install elsewhere:

1. Clone the repository to your desired location
2. Run the unified installer from that directory

### Environment Variables

You can customize behavior with environment variables:

```bash
# Skip Node.js installation check
SKIP_NODE_CHECK=true ./install-unified.sh

# Use specific Python version
PYTHON_CMD=/usr/local/bin/python3.11 ./install-unified.sh
```

### Silent Installation

For automated setups, the installer will run non-interactively:

```bash
# Automatically starts servers
./install-unified.sh

# Installs without starting
./install-unified.sh --no-start
```

## Integration with CI/CD

The unified installer can be used in CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Install Reasoning Core
  run: ./install-unified.sh --no-start

- name: Start servers
  run: ./start.sh &
```

## Next Steps

- Read [QUICK_START.md](../QUICK_START.md) for getting started quickly
- Read [LOCAL_INSTALL.md](../LOCAL_INSTALL.md) for detailed installation options
- Check [installers/BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md) for building platform-specific installers

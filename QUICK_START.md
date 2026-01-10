# Quick Start Guide

Get Reasoning Core up and running in seconds!

## 🚀 One-Command Setup

### macOS/Linux

```bash
./install-unified.sh
```

### Windows

```cmd
install-unified.bat
```

That's it! The unified installer will:
1. ✅ Check for Python and Node.js
2. ✅ Install all dependencies automatically
3. ✅ Start the servers automatically
4. ✅ Open the web interface

## 📍 Access Your Application

After installation, access:

- **🌐 Web UI**: http://localhost:3000
- **🔌 API Server**: http://localhost:8000
- **📚 API Documentation**: http://localhost:8000/docs

## 🛑 Stopping the Servers

- **macOS/Linux**: Press `Ctrl+C` in the terminal
- **Windows**: Close the command windows that opened

## ▶️ Restarting After Installation

If you need to restart the servers later:

### macOS/Linux

```bash
./start.sh
```

### Windows

```cmd
start.bat
```

## 📦 Installation Without Auto-Start

If you want to install dependencies but not start the servers immediately:

### macOS/Linux

```bash
./install-unified.sh --no-start
```

### Windows

```cmd
install-unified.bat --no-start
```

## 🔧 Troubleshooting

### Python Not Found

**macOS/Linux:**
```bash
# Install via Homebrew (macOS)
brew install python@3.11

# Or download from python.org
```

**Windows:**
- Download from https://www.python.org/downloads/
- Make sure to check "Add Python to PATH" during installation

### Node.js Not Found

**macOS/Linux:**
```bash
# Install via Homebrew (macOS)
brew install node

# Or download from nodejs.org
```

**Windows:**
- Download from https://nodejs.org/
- Install the LTS version

### Port Already in Use

If ports 8000 or 3000 are already in use:
- Stop other applications using those ports
- Or modify the ports in the configuration files

### Permission Errors

**macOS/Linux:**
- Use `sudo` only if necessary
- Consider using a virtual environment

**Windows:**
- Run Command Prompt/PowerShell as Administrator

## 📖 Next Steps

- Check out the [README](README.md) for usage examples
- Explore the [API documentation](http://localhost:8000/docs) when running
- Read [LOCAL_INSTALL.md](LOCAL_INSTALL.md) for detailed installation options

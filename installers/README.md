# Reasoning Core Installers

Cross-platform installer packages for Reasoning Core that automatically install all dependencies.

## Supported Platforms

- **macOS**: `.pkg` installer package
- **Windows**: `.exe` installer (Inno Setup)

## Building Installers

### macOS

1. Make sure you're on macOS:
```bash
cd installers/macos
./build-pkg.sh
```

The installer will be created at: `installers/macos/build/ReasoningCore-0.1.0-macos.pkg`

**Requirements:**
- macOS with Xcode Command Line Tools (`xcode-select --install`)
- `pkgbuild` and `productbuild` (included with macOS)

### Windows

1. Install [Inno Setup 6](https://jrsoftware.org/isdl.php)

2. Build the installer:
```batch
cd installers\windows
build-installer.bat
```

The installer will be created at: `installers/windows/build/ReasoningCore-0.1.0-windows-setup.exe`

**Requirements:**
- Windows 10/11 (64-bit)
- Inno Setup 6
- Administrator privileges (for building and installing)

### Build All (macOS/Linux)

```bash
./installers/build-all.sh
```

## Installer Features

### Automatic Dependency Installation

Both installers automatically:

1. **Check and install Python 3.9+** (if not present)
   - macOS: Via Homebrew
   - Windows: Downloads and installs Python 3.11

2. **Install Python packages:**
   - pydantic, fastapi, uvicorn
   - requests, beautifulsoup4
   - PyPDF2, python-docx
   - reasoning-core itself

3. **Check and install Node.js** (if not present)
   - macOS: Via Homebrew
   - Windows: Downloads and installs Node.js LTS

4. **Install frontend dependencies:**
   - React, Vite, Tailwind CSS
   - Cytoscape.js for graph visualization
   - All npm packages

### What Gets Installed

**macOS:**
- Installation directory: `/Applications/ReasoningCore`
- Command line tool: `/usr/local/bin/reasoning-core`

**Windows:**
- Installation directory: `C:\Program Files\ReasoningCore`
- Desktop shortcut (optional)
- Start menu entry

### Starting the Application

**macOS:**
```bash
reasoning-core
# Or
/Applications/ReasoningCore/start_server.sh
```

**Windows:**
- Double-click `ReasoningCore.bat` from the installation directory
- Or use the Start Menu shortcut
- Or run from command line: `"C:\Program Files\ReasoningCore\start_server.bat"`

### Access Points

After installation, the application is available at:

- **API Server**: http://localhost:8000
- **Web UI**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs

## Development Notes

### macOS Installer Structure

```
installers/macos/
├── build-pkg.sh           # Main build script
├── install_dependencies.sh # Dependency installer
├── postinstall.sh          # Post-install script
├── start_server.sh         # Server launcher
└── scripts/
    └── postinstall         # pkgbuild postinstall script
```

### Windows Installer Structure

```
installers/windows/
├── build-installer.bat     # Main build script
├── installer.iss           # Inno Setup script
├── install_dependencies.ps1 # PowerShell dependency installer
└── start_server.bat        # Server launcher
```

## Customization

### Changing Installation Directory

**macOS**: Edit `build-pkg.sh` and change `INSTALL_DIR` variable

**Windows**: Edit `installer.iss` and change `DefaultDirName` value

### Adding Additional Dependencies

**Python packages**: Add to `install_dependencies.sh` (macOS) or `install_dependencies.ps1` (Windows)

**Node packages**: They're installed from `package.json` automatically

## Troubleshooting

### macOS

**Issue**: "pkgbuild: command not found"
- Solution: Install Xcode Command Line Tools: `xcode-select --install`

**Issue**: Installer fails silently
- Check: `/tmp/reasoning-core-install.log` for installation logs

### Windows

**Issue**: "Inno Setup Compiler not found"
- Solution: Install Inno Setup 6 and update the path in `build-installer.bat`

**Issue**: Python/Node.js not installing
- Check: Run PowerShell as Administrator
- Check: Windows Defender / Antivirus isn't blocking downloads

## Testing Installers

### macOS

```bash
# Build installer
./installers/macos/build-pkg.sh

# Install (test)
open installers/macos/build/ReasoningCore-0.1.0-macos.pkg

# Or via command line
sudo installer -pkg installers/macos/build/ReasoningCore-0.1.0-macos.pkg -target /
```

### Windows

1. Build installer
2. Right-click the `.exe` → "Run as Administrator"
3. Follow the installation wizard

## Distribution

The installers can be distributed independently:

- **macOS**: Share the `.pkg` file (code signing recommended for distribution)
- **Windows**: Share the `.exe` file

Users only need to:
1. Download the installer
2. Run it
3. Follow the prompts

All dependencies are installed automatically!

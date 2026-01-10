# Building Installers for macOS and Windows

This guide explains how to build installer packages for Reasoning Core on macOS and Windows.

## macOS Installer (.pkg)

### Prerequisites

- macOS with Xcode Command Line Tools installed
- `pkgbuild` and `productbuild` (included with macOS)

Install Xcode Command Line Tools if needed:
```bash
xcode-select --install
```

### Building the Installer

1. Navigate to the installers directory:
```bash
cd installers/macos
```

2. Run the build script:
```bash
./build-pkg.sh
```

3. The installer will be created at:
   ```
   installers/macos/build/ReasoningCore-0.1.0-macos.pkg
   ```

### What the Installer Does

- Installs Reasoning Core to `/Applications/ReasoningCore`
- Creates a command-line shortcut: `/usr/local/bin/reasoning-core`
- Installs all Python dependencies automatically
- Installs all Node.js dependencies automatically (if Node.js is available)
- Sets up the application for immediate use

### Installing the Package

1. Double-click the `.pkg` file, or
2. Use command line:
```bash
sudo installer -pkg installers/macos/build/ReasoningCore-0.1.0-macos.pkg -target /
```

### After Installation

Start Reasoning Core:
```bash
reasoning-core
```

Or navigate to `/Applications/ReasoningCore` and run:
```bash
./start_server.sh
```

## Windows Installer (.exe)

### Prerequisites

- Windows 10/11 (64-bit)
- [Inno Setup 6](https://jrsoftware.org/isdl.php) installed
- Administrator privileges

### Installing Inno Setup

1. Download Inno Setup 6 from: https://jrsoftware.org/isdl.php
2. Install it (default location: `C:\Program Files (x86)\Inno Setup 6\`)

### Building the Installer

1. Open Command Prompt or PowerShell as Administrator
2. Navigate to the installers directory:
```cmd
cd installers\windows
```

3. Run the build script:
```cmd
build-installer.bat
```

4. The installer will be created at:
   ```
   installers\windows\build\ReasoningCore-0.1.0-windows-setup.exe
   ```

### What the Installer Does

- Installs Reasoning Core to `C:\Program Files\ReasoningCore` (or chosen directory)
- Creates Start Menu shortcuts
- Optionally creates a desktop shortcut
- Installs Python 3.11 automatically (if not present)
- Installs Node.js LTS automatically (if not present)
- Installs all Python dependencies automatically
- Installs all Node.js dependencies automatically

### Installing the Package

1. Right-click the `.exe` file
2. Select "Run as Administrator"
3. Follow the installation wizard

### After Installation

Start Reasoning Core from:
- Start Menu → Reasoning Core
- Desktop shortcut (if created)
- Or run: `C:\Program Files\ReasoningCore\start_server.bat`

## Build All (macOS/Linux)

On macOS or Linux, you can use the convenience script:

```bash
./installers/build-all.sh
```

This will automatically detect your platform and build the appropriate installer.

## Testing Installers

### macOS

1. Build the installer as described above
2. Test installation:
```bash
# Install to a test location
mkdir -p /tmp/reasoning-test
sudo installer -pkg installers/macos/build/ReasoningCore-0.1.0-macos.pkg -target /tmp/reasoning-test
```

### Windows

1. Build the installer as described above
2. Right-click the `.exe` → "Run as Administrator"
3. Follow the installation wizard
4. Test that the application starts correctly

## Customization

### Changing Installation Directory

**macOS**: Edit `installers/macos/build-pkg.sh` and change:
```bash
INSTALL_DIR="Applications/ReasoningCore"
```

**Windows**: Edit `installers/windows/installer.iss` and change:
```ini
DefaultDirName={autopf}\ReasoningCore
```

### Changing Version Number

Update the version in:
- `pyproject.toml` (main version)
- `installers/macos/build-pkg.sh` (PKG version)
- `installers/windows/installer.iss` (AppVersion)

### Adding Additional Dependencies

**Python packages**: Add to:
- `requirements-web.txt` (for web dependencies)
- `pyproject.toml` (for core dependencies)

**Node.js packages**: Add to `web/package.json`

The installers will automatically install these when they run.

## Distribution

### macOS

- Share the `.pkg` file
- For wider distribution, consider code signing (requires Apple Developer account)
- Users can double-click to install

### Windows

- Share the `.exe` file
- Users should run as Administrator
- No additional signing required (but signing improves trust)

## Troubleshooting

### macOS Build Issues

**"pkgbuild: command not found"**
- Install Xcode Command Line Tools: `xcode-select --install`

**"Permission denied"**
- Make scripts executable: `chmod +x installers/macos/build-pkg.sh`
- Ensure you have write permissions to the build directory

### Windows Build Issues

**"Inno Setup Compiler not found"**
- Verify Inno Setup 6 is installed
- Update the path in `build-installer.bat` if installed to a different location

**"Access denied"**
- Run Command Prompt/PowerShell as Administrator

### Installation Issues

**Python/Node.js not installing automatically**
- Check internet connection
- Verify installer has network permissions
- Try installing Python/Node.js manually first

**Dependencies not installing**
- Check that pip/npm are in PATH
- Verify Python/Node.js versions meet requirements
- Check installer logs (usually in system temp directory)

## Advanced Options

### Silent Installation (macOS)

```bash
sudo installer -pkg installer.pkg -target / -allowUntrusted
```

### Silent Installation (Windows)

```cmd
installer.exe /SILENT /DIR="C:\Custom\Path"
```

### Uninstallation

**macOS**: 
- Delete `/Applications/ReasoningCore`
- Delete `/usr/local/bin/reasoning-core` symlink

**Windows**:
- Use "Add or Remove Programs"
- Or run: `C:\Program Files\ReasoningCore\uninstall.exe` (if created)

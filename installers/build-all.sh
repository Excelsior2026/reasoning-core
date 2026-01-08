#!/bin/bash
# Build installers for all platforms

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "🏗️  Building Reasoning Core Installers"
echo ""

# Detect platform
PLATFORM="$(uname -s)"
case "$PLATFORM" in
    Darwin*)
        echo "🍎 Detected macOS"
        echo "Building macOS installer..."
        "$SCRIPT_DIR/macos/build-pkg.sh"
        ;;
    Linux*)
        echo "🐧 Detected Linux"
        echo "Linux installer not yet implemented"
        ;;
    MINGW*|MSYS*|CYGWIN*)
        echo "🪟 Detected Windows (via Git Bash)"
        echo "Please run build-installer.bat from Windows"
        ;;
    *)
        echo "❓ Unknown platform: $PLATFORM"
        exit 1
        ;;
esac

echo ""
echo "✅ Build complete!"

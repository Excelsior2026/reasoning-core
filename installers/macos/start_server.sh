#!/bin/bash
# Start Reasoning Core web server (macOS)

set -e

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
INSTALL_DIR="$SCRIPT_DIR"

# Find Python 3
PYTHON3=$(which python3 2>/dev/null || which python 2>/dev/null || echo "")

if [ -z "$PYTHON3" ] || [ ! -f "$PYTHON3" ]; then
    echo "❌ Python 3 not found. Please install Python 3.9 or later."
    echo "   You can install it via Homebrew: brew install python@3.11"
    exit 1
fi

# Verify reasoning-core is installed
if ! $PYTHON3 -c "import reasoning_core" 2>/dev/null; then
    echo "⚠️  reasoning-core not found. Installing dependencies..."
    if [ -f "$INSTALL_DIR/install_dependencies.sh" ]; then
        "$INSTALL_DIR/install_dependencies.sh" "$INSTALL_DIR"
    else
        $PYTHON3 -m pip install -e "$INSTALL_DIR" || $PYTHON3 -m pip install reasoning-core
    fi
fi

echo "🧠 Starting Reasoning Core Web Server..."
echo ""
echo "📍 API Server: http://localhost:8000"
echo "🌐 Web UI: http://localhost:3000 (run in separate terminal: cd $INSTALL_DIR/web && npm run dev)"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Change to install directory
cd "$INSTALL_DIR"

# Start backend server
$PYTHON3 -m reasoning_core.web.server

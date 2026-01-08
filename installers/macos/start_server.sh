#!/bin/bash
# Start Reasoning Core web server (macOS)

set -e

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
INSTALL_DIR="$(dirname "$SCRIPT_DIR")"

# Set Python path
export PYTHONPATH="$INSTALL_DIR/lib/python:$PYTHONPATH"

# Find Python 3
PYTHON3=$(which python3 2>/dev/null || echo "/usr/bin/python3")

if [ ! -f "$PYTHON3" ]; then
    echo "❌ Python 3 not found. Please install Python 3.9 or later."
    exit 1
fi

echo "🧠 Starting Reasoning Core Web Server..."
echo ""
echo "📍 API Server: http://localhost:8000"
echo "🌐 Web UI: http://localhost:3000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start backend server in background
cd "$INSTALL_DIR"
$PYTHON3 -m reasoning_core.web.server &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 2

# Start frontend if it exists
if [ -d "$INSTALL_DIR/web" ] && [ -d "$INSTALL_DIR/web/node_modules" ]; then
    cd "$INSTALL_DIR/web"
    if command -v npm >/dev/null 2>&1; then
        echo "Starting frontend..."
        npm run dev &
        FRONTEND_PID=$!
    fi
fi

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Stopping servers..."
    kill $BACKEND_PID 2>/dev/null || true
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    exit 0
}

trap cleanup SIGINT SIGTERM

# Wait for processes
wait

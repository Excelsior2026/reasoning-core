#!/bin/bash
# Quick start script for Reasoning Core (macOS/Linux)

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🧠 Starting Reasoning Core...${NC}"
echo ""

# Find Python
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo -e "${RED}✗ Python not found. Run ./install-unified.sh first${NC}"
    exit 1
fi

# Check if reasoning-core is installed
if ! $PYTHON_CMD -c "import reasoning_core" 2>/dev/null; then
    echo -e "${YELLOW}⚠ reasoning-core not installed. Running installer...${NC}"
    echo ""
    ./install-unified.sh
    exit $?
fi

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Stopping servers...${NC}"
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start backend server
echo -e "${GREEN}🚀 Starting API server on http://localhost:8000${NC}"
$PYTHON_CMD -m reasoning_core.web.server &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start frontend if available
if command -v npm &> /dev/null && [ -d "web" ] && [ -d "web/node_modules" ]; then
    echo -e "${GREEN}🌐 Starting Web UI on http://localhost:3000${NC}"
    cd web
    npm run dev &
    FRONTEND_PID=$!
    cd ..
fi

echo ""
echo -e "${GREEN}✅ Servers started!${NC}"
echo ""
echo -e "${BLUE}📍 Access points:${NC}"
echo -e "   API Server: ${GREEN}http://localhost:8000${NC}"
if command -v npm &> /dev/null && [ -d "web/node_modules" ]; then
    echo -e "   Web UI:     ${GREEN}http://localhost:3000${NC}"
fi
echo -e "   API Docs:   ${GREEN}http://localhost:8000/docs${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the servers${NC}"
echo ""

# Wait for processes
wait

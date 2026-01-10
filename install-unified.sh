#!/bin/bash
# Unified installer and launcher for Reasoning Core (macOS/Linux)

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${BLUE}🧠 Reasoning Core - Unified Installer & Launcher${NC}"
echo "=============================================="
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Python
echo -e "${BLUE}Checking Python...${NC}"
if command_exists python3; then
    PYTHON_CMD="python3"
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
    echo -e "${GREEN}✓ Python ${PYTHON_VERSION} found${NC}"
    
    # Check version
    MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 9 ]); then
        echo -e "${RED}✗ Python 3.9+ required. Found ${PYTHON_VERSION}${NC}"
        exit 1
    fi
elif command_exists python; then
    PYTHON_CMD="python"
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
    echo -e "${GREEN}✓ Python ${PYTHON_VERSION} found${NC}"
else
    echo -e "${RED}✗ Python 3.9+ not found. Please install Python first.${NC}"
    exit 1
fi

# Check pip
echo -e "${BLUE}Checking pip...${NC}"
if $PYTHON_CMD -m pip --version >/dev/null 2>&1; then
    echo -e "${GREEN}✓ pip found${NC}"
    PIP_CMD="$PYTHON_CMD -m pip"
else
    echo -e "${RED}✗ pip not found. Please install pip first.${NC}"
    exit 1
fi

# Check Node.js
NODE_AVAILABLE=false
echo -e "${BLUE}Checking Node.js...${NC}"
if command_exists node; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✓ Node.js ${NODE_VERSION} found${NC}"
    if command_exists npm; then
        NPM_VERSION=$(npm --version)
        echo -e "${GREEN}✓ npm ${NPM_VERSION} found${NC}"
        NODE_AVAILABLE=true
    else
        echo -e "${YELLOW}⚠ npm not found. Web UI will not be available.${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Node.js not found. Web UI will not be available.${NC}"
    echo -e "${YELLOW}  Install Node.js from https://nodejs.org/ for full functionality${NC}"
fi

echo ""
echo -e "${BLUE}Installing/Updating dependencies...${NC}"
echo ""

# Upgrade pip
$PIP_CMD install --upgrade pip --quiet

# Install Python dependencies
echo -e "${BLUE}Installing Python packages...${NC}"
$PIP_CMD install -e . --quiet
$PIP_CMD install -r requirements-web.txt --quiet

echo -e "${GREEN}✓ Python dependencies installed${NC}"
echo ""

# Install Node.js dependencies
if [ "$NODE_AVAILABLE" = true ] && [ -d "web" ]; then
    echo -e "${BLUE}Installing Node.js packages...${NC}"
    cd web
    npm install --silent
    cd ..
    echo -e "${GREEN}✓ Node.js dependencies installed${NC}"
    echo ""
fi

echo -e "${GREEN}=============================================="
echo -e "Installation Complete! 🎉${NC}"
echo -e "${GREEN}==============================================${NC}"
echo ""

# Check if user wants to start server
if [ -z "$1" ] || [ "$1" != "--no-start" ]; then
    echo -e "${BLUE}Starting Reasoning Core servers...${NC}"
    echo ""
    
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
    if [ "$NODE_AVAILABLE" = true ] && [ -d "web" ]; then
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
    if [ "$NODE_AVAILABLE" = true ]; then
        echo -e "   Web UI:     ${GREEN}http://localhost:3000${NC}"
    fi
    echo -e "   API Docs:   ${GREEN}http://localhost:8000/docs${NC}"
    echo ""
    echo -e "${YELLOW}Press Ctrl+C to stop the servers${NC}"
    echo ""
    
    # Wait for processes
    wait
else
    echo -e "${BLUE}To start the servers, run:${NC}"
    echo -e "  ${GREEN}./install-unified.sh${NC}"
    echo ""
    echo "Or manually:"
    echo "  Terminal 1: $PYTHON_CMD -m reasoning_core.web.server"
    if [ "$NODE_AVAILABLE" = true ]; then
        echo "  Terminal 2: cd web && npm run dev"
    fi
fi

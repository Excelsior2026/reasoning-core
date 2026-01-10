#!/bin/bash
# Simplified local installation script for Reasoning Core

set -e

echo "🧠 Reasoning Core - Local Installation Script"
echo "=============================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Python is installed
echo -e "${BLUE}Checking Python installation...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    echo -e "${GREEN}✓ Python ${PYTHON_VERSION} found${NC}"
    
    # Check if version is 3.9+
    MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 9 ]); then
        echo -e "${RED}✗ Python 3.9+ required. Found ${PYTHON_VERSION}${NC}"
        exit 1
    fi
else
    echo -e "${RED}✗ Python 3.9+ not found. Please install Python first.${NC}"
    exit 1
fi

# Check if pip is installed
echo -e "${BLUE}Checking pip installation...${NC}"
if command -v pip3 &> /dev/null; then
    echo -e "${GREEN}✓ pip3 found${NC}"
    PIP_CMD="pip3"
elif python3 -m pip --version &> /dev/null; then
    echo -e "${GREEN}✓ pip found via python3 -m pip${NC}"
    PIP_CMD="python3 -m pip"
else
    echo -e "${RED}✗ pip not found. Please install pip first.${NC}"
    exit 1
fi

# Check if Node.js is installed
echo -e "${BLUE}Checking Node.js installation...${NC}"
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✓ Node.js ${NODE_VERSION} found${NC}"
else
    echo -e "${YELLOW}⚠ Node.js not found. Web UI will not be available.${NC}"
    echo -e "${YELLOW}  Install Node.js from https://nodejs.org/ for full functionality${NC}"
    NODE_AVAILABLE=false
fi

# Check if npm is installed
if [ "$NODE_AVAILABLE" != "false" ]; then
    echo -e "${BLUE}Checking npm installation...${NC}"
    if command -v npm &> /dev/null; then
        NPM_VERSION=$(npm --version)
        echo -e "${GREEN}✓ npm ${NPM_VERSION} found${NC}"
    else
        echo -e "${YELLOW}⚠ npm not found. Web UI will not be available.${NC}"
        NODE_AVAILABLE=false
    fi
fi

echo ""
echo -e "${BLUE}Installing Python dependencies...${NC}"
echo ""

# Upgrade pip
echo -e "${BLUE}Upgrading pip...${NC}"
$PIP_CMD install --upgrade pip --quiet

# Install Python dependencies
echo -e "${BLUE}Installing Python packages...${NC}"
$PIP_CMD install -e . --quiet

# Install web dependencies if requirements-web.txt exists
if [ -f "requirements-web.txt" ]; then
    echo -e "${BLUE}Installing web dependencies...${NC}"
    $PIP_CMD install -r requirements-web.txt --quiet
fi

echo ""
echo -e "${GREEN}✓ Python dependencies installed${NC}"
echo ""

# Install Node.js dependencies for web UI
if [ "$NODE_AVAILABLE" != "false" ] && [ -d "web" ]; then
    echo -e "${BLUE}Installing Node.js dependencies...${NC}"
    cd web
    if [ -f "package.json" ]; then
        npm install --silent
        echo -e "${GREEN}✓ Node.js dependencies installed${NC}"
    fi
    cd ..
    echo ""
fi

# Make run scripts executable
if [ -f "run_web.sh" ]; then
    chmod +x run_web.sh
fi

echo ""
echo -e "${GREEN}=============================================="
echo -e "Installation Complete! 🎉${NC}"
echo -e "${GREEN}==============================================${NC}"
echo ""
echo "To start the Reasoning Core server:"
echo ""
echo "  1. Start the API server:"
echo -e "     ${BLUE}python -m reasoning_core.web.server${NC}"
echo ""
if [ "$NODE_AVAILABLE" != "false" ]; then
    echo "  2. In another terminal, start the web UI:"
    echo -e "     ${BLUE}cd web && npm run dev${NC}"
    echo ""
    echo "  3. Open your browser to:"
    echo -e "     ${BLUE}http://localhost:3000${NC}"
    echo ""
fi
echo "  4. API documentation available at:"
echo -e "     ${BLUE}http://localhost:8000/docs${NC}"
echo ""
echo -e "Or use the convenience script:"
echo -e "  ${BLUE}./run_web.sh${NC}"
echo ""

#!/bin/bash
# Install dependencies for reasoning-core on macOS

set -e

echo "🧠 Installing Reasoning Core Dependencies..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root (not recommended, but handle it)
if [ "$EUID" -eq 0 ]; then
    echo -e "${YELLOW}Warning: Running as root. Some operations may need sudo.${NC}"
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for Homebrew
if ! command_exists brew; then
    echo -e "${YELLOW}Homebrew not found. Installing Homebrew...${NC}"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add Homebrew to PATH for Apple Silicon Macs
    if [ -f "/opt/homebrew/bin/brew" ]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
    fi
fi

# Install Python 3.11+ if not present
if ! command_exists python3; then
    echo -e "${YELLOW}Python 3 not found. Installing via Homebrew...${NC}"
    brew install python@3.11
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"

# Ensure pip is installed and up to date
python3 -m pip install --upgrade pip setuptools wheel

# Install Node.js if not present
if ! command_exists node; then
    echo -e "${YELLOW}Node.js not found. Installing via Homebrew...${NC}"
    brew install node
fi

NODE_VERSION=$(node --version)
echo -e "${GREEN}✓ Node.js $NODE_VERSION found${NC}"

# Install npm if not present (usually comes with Node.js)
if ! command_exists npm; then
    echo -e "${YELLOW}npm not found. Installing...${NC}"
    brew install npm
fi

NPM_VERSION=$(npm --version)
echo -e "${GREEN}✓ npm $NPM_VERSION found${NC}"

# Get the script directory (installer package directory)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
INSTALL_DIR="${1:-/Applications/ReasoningCore}"

echo ""
echo "📦 Installing Python dependencies..."

# Create lib/python directory if it doesn't exist
mkdir -p "$INSTALL_DIR/lib/python"

# Install Python packages to a location that can be in PYTHONPATH
python3 -m pip install --upgrade \
    pydantic>=2.0.0 \
    fastapi>=0.100.0 \
    uvicorn[standard]>=0.23.0 \
    python-multipart>=0.0.6 \
    requests>=2.31.0 \
    beautifulsoup4>=4.12.0 \
    PyPDF2>=3.0.0 \
    python-docx>=1.0.0 \
    aiofiles>=23.0.0 \
    pyjwt>=2.8.0 \
    "python-jose[cryptography]>=3.3.0" \
    --upgrade-strategy only-if-needed

# Also install reasoning-core itself (in editable mode if source exists, otherwise from package)
if [ -d "$INSTALL_DIR/src" ]; then
    echo "📦 Installing reasoning-core from source..."
    cd "$INSTALL_DIR"
    python3 -m pip install -e . --upgrade-strategy only-if-needed
elif [ -d "$SCRIPT_DIR/../../src" ]; then
    echo "📦 Installing reasoning-core from source..."
    python3 -m pip install -e "$SCRIPT_DIR/../.." --upgrade-strategy only-if-needed
else
    echo "📦 Installing reasoning-core from package..."
    python3 -m pip install reasoning-core --upgrade
fi

echo ""
echo "📦 Installing Node.js dependencies..."

# Install frontend dependencies
if [ -d "$INSTALL_DIR/web" ]; then
    cd "$INSTALL_DIR/web"
    npm install --production --legacy-peer-deps
fi

echo ""
echo -e "${GREEN}✅ All dependencies installed successfully!${NC}"
echo ""
echo "Installation location: $INSTALL_DIR"
echo ""
echo "To start the server:"
echo "  $INSTALL_DIR/start_server.sh"

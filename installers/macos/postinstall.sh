#!/bin/bash
# Post-install script for macOS installer package

set -e

INSTALL_DIR="$1"

if [ -z "$INSTALL_DIR" ]; then
    INSTALL_DIR="/Applications/ReasoningCore"
fi

echo "🔧 Running post-install configuration..."

# Make scripts executable
chmod +x "$INSTALL_DIR/start_server.sh" 2>/dev/null || true
chmod +x "$INSTALL_DIR/install-unified.sh" 2>/dev/null || true
chmod +x "$INSTALL_DIR/start.sh" 2>/dev/null || true
chmod +x "$INSTALL_DIR/installers/macos/install_dependencies.sh" 2>/dev/null || true

# Run dependency installation
"$INSTALL_DIR/installers/macos/install_dependencies.sh" "$INSTALL_DIR"

# Create symlink to start command
if [ ! -f "/usr/local/bin/reasoning-core" ]; then
    ln -sf "$INSTALL_DIR/start_server.sh" /usr/local/bin/reasoning-core
    chmod +x /usr/local/bin/reasoning-core
fi

echo "✅ Installation complete!"
echo ""
echo "Starting Reasoning Core servers..."
echo ""

# Ask user if they want to start servers
if [ -t 0 ]; then
    # Interactive mode - ask user
    read -p "Start servers now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cd "$INSTALL_DIR"
        ./start.sh &
        echo ""
        echo "✅ Servers starting in background!"
        echo ""
        echo "📍 Access points:"
        echo "   API Server: http://localhost:8000"
        echo "   Web UI:     http://localhost:3000"
        echo "   API Docs:   http://localhost:8000/docs"
        echo ""
    fi
else
    # Non-interactive mode - start automatically
    cd "$INSTALL_DIR"
    ./start.sh &
    echo ""
    echo "✅ Servers starting in background!"
    echo ""
    echo "📍 Access points:"
    echo "   API Server: http://localhost:8000"
    echo "   Web UI:     http://localhost:3000"
    echo "   API Docs:   http://localhost:8000/docs"
    echo ""
fi

echo "To start Reasoning Core manually, run:"
echo "  reasoning-core"
echo "  or"
echo "  cd $INSTALL_DIR && ./start.sh"

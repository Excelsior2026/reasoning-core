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
echo "To start Reasoning Core, run:"
echo "  reasoning-core"
echo ""
echo "Or open: $INSTALL_DIR/ReasoningCore.app"

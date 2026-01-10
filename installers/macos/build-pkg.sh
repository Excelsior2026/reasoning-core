#!/bin/bash
# Build macOS installer package (.pkg)

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
BUILD_DIR="$SCRIPT_DIR/build"
PKG_BUILD_DIR="$BUILD_DIR/pkg"
PAYLOAD_DIR="$PKG_BUILD_DIR/payload"

# Clean previous builds
rm -rf "$BUILD_DIR"
mkdir -p "$PAYLOAD_DIR"

echo "📦 Building macOS installer package..."
echo ""

# Install directory
INSTALL_DIR="Applications/ReasoningCore"

# Create installation structure
mkdir -p "$PAYLOAD_DIR/$INSTALL_DIR"

# Copy source files
echo "📋 Copying source files..."
cp -r "$PROJECT_ROOT/src" "$PAYLOAD_DIR/$INSTALL_DIR/"
cp "$PROJECT_ROOT/pyproject.toml" "$PAYLOAD_DIR/$INSTALL_DIR/" 2>/dev/null || true
cp "$PROJECT_ROOT/requirements-web.txt" "$PAYLOAD_DIR/$INSTALL_DIR/" 2>/dev/null || true

# Copy web frontend
if [ -d "$PROJECT_ROOT/web" ]; then
    echo "🌐 Copying web frontend..."
    cp -r "$PROJECT_ROOT/web" "$PAYLOAD_DIR/$INSTALL_DIR/"
    # Don't copy node_modules - will be installed
    rm -rf "$PAYLOAD_DIR/$INSTALL_DIR/web/node_modules" 2>/dev/null || true
    rm -rf "$PAYLOAD_DIR/$INSTALL_DIR/web/dist" 2>/dev/null || true
    rm -rf "$PAYLOAD_DIR/$INSTALL_DIR/web/.vite" 2>/dev/null || true
fi

# Copy installation scripts
if [ -f "$PROJECT_ROOT/install.sh" ]; then
    cp "$PROJECT_ROOT/install.sh" "$PAYLOAD_DIR/$INSTALL_DIR/"
    chmod +x "$PAYLOAD_DIR/$INSTALL_DIR/install.sh"
fi

if [ -f "$PROJECT_ROOT/install-unified.sh" ]; then
    cp "$PROJECT_ROOT/install-unified.sh" "$PAYLOAD_DIR/$INSTALL_DIR/"
    chmod +x "$PAYLOAD_DIR/$INSTALL_DIR/install-unified.sh"
fi

if [ -f "$PROJECT_ROOT/start.sh" ]; then
    cp "$PROJECT_ROOT/start.sh" "$PAYLOAD_DIR/$INSTALL_DIR/"
    chmod +x "$PAYLOAD_DIR/$INSTALL_DIR/start.sh"
fi

if [ -f "$PROJECT_ROOT/run_web.sh" ]; then
    cp "$PROJECT_ROOT/run_web.sh" "$PAYLOAD_DIR/$INSTALL_DIR/"
    chmod +x "$PAYLOAD_DIR/$INSTALL_DIR/run_web.sh"
fi

# Copy installer scripts
echo "🔧 Copying installer scripts..."
mkdir -p "$PAYLOAD_DIR/$INSTALL_DIR/installers/macos"
cp "$SCRIPT_DIR/install_dependencies.sh" "$PAYLOAD_DIR/$INSTALL_DIR/installers/macos/"
cp "$SCRIPT_DIR/postinstall.sh" "$PAYLOAD_DIR/$INSTALL_DIR/installers/macos/"
cp "$SCRIPT_DIR/start_server.sh" "$PAYLOAD_DIR/$INSTALL_DIR/"

# Make scripts executable
chmod +x "$PAYLOAD_DIR/$INSTALL_DIR/start_server.sh"
chmod +x "$PAYLOAD_DIR/$INSTALL_DIR/installers/macos/install_dependencies.sh"
chmod +x "$PAYLOAD_DIR/$INSTALL_DIR/installers/macos/postinstall.sh"

# Create Distribution XML
cat > "$PKG_BUILD_DIR/Distribution.xml" <<EOF
<?xml version="1.0" encoding="utf-8"?>
<installer-gui-script minSpecVersion="1">
    <title>Reasoning Core</title>
    <organization>com.reasoningcore</organization>
    <domains enable_localSystem="true"/>
    <options customize="never" require-scripts="false" rootVolumeOnly="true" />
    <welcome file="Welcome.txt" mime-type="text/plain" />
    <license file="License.txt" mime-type="text/plain" />
    <conclusion file="Conclusion.txt" mime-type="text/plain" />
    <pkg-ref id="com.reasoningcore.pkg"/>
    <choices-outline>
        <line choice="default">
            <line choice="com.reasoningcore.pkg"/>
        </line>
    </choices-outline>
    <choice id="default"/>
    <choice id="com.reasoningcore.pkg" visible="false">
        <pkg-ref id="com.reasoningcore.pkg"/>
    </choice>
    <pkg-ref id="com.reasoningcore.pkg" version="0.1.0" onConclusion="none">reasoning-core.pkg</pkg-ref>
</installer-gui-script>
EOF

# Create welcome/license/conclusion files
cat > "$PKG_BUILD_DIR/Welcome.txt" <<EOF
Welcome to Reasoning Core!

This installer will set up Reasoning Core, a universal reasoning extraction engine 
that transforms documents, websites, and text into intelligent knowledge graphs.

The installer will:
- Install Python dependencies
- Install Node.js dependencies (for the web UI)
- Set up the application

Please note: This installation may take a few minutes to download and install 
all required dependencies.
EOF

cat > "$PKG_BUILD_DIR/License.txt" <<EOF
MIT License

Copyright (c) 2026 Excelsior2026

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction...
EOF

cat > "$PKG_BUILD_DIR/Conclusion.txt" <<EOF
Installation Complete!

Reasoning Core has been successfully installed.

To start the application:
1. Open Terminal
2. Run: reasoning-core

Or navigate to /Applications/ReasoningCore and double-click start_server.sh

The web interface will be available at:
- API Server: http://localhost:8000
- Web UI: http://localhost:3000
EOF

# Build component package
echo "🔨 Building component package..."
pkgbuild \
    --root "$PAYLOAD_DIR" \
    --identifier "com.reasoningcore.pkg" \
    --version "0.1.0" \
    --install-location "/" \
    --scripts "$SCRIPT_DIR/scripts" \
    "$PKG_BUILD_DIR/reasoning-core.pkg"

# Create scripts directory
mkdir -p "$SCRIPT_DIR/scripts"

# Create postinstall script for pkgbuild
cat > "$SCRIPT_DIR/scripts/postinstall" <<EOF
#!/bin/bash
# Post-install script for pkgbuild

INSTALL_DIR="/Applications/ReasoningCore"

# Make scripts executable
chmod +x "\$INSTALL_DIR/start_server.sh"
chmod +x "\$INSTALL_DIR/installers/macos/install_dependencies.sh"

# Run dependency installation (in background to not block installer)
"\$INSTALL_DIR/installers/macos/install_dependencies.sh" "\$INSTALL_DIR" > /tmp/reasoning-core-install.log 2>&1 &

# Create symlink
mkdir -p /usr/local/bin
if [ ! -f "/usr/local/bin/reasoning-core" ]; then
    ln -sf "\$INSTALL_DIR/start_server.sh" /usr/local/bin/reasoning-core
fi

exit 0
EOF

chmod +x "$SCRIPT_DIR/scripts/postinstall"

# Rebuild with scripts
pkgbuild \
    --root "$PAYLOAD_DIR" \
    --identifier "com.reasoningcore.pkg" \
    --version "0.1.0" \
    --install-location "/" \
    --scripts "$SCRIPT_DIR/scripts" \
    "$PKG_BUILD_DIR/reasoning-core.pkg"

# Build final installer
echo "🎁 Creating final installer..."
productbuild \
    --distribution "$PKG_BUILD_DIR/Distribution.xml" \
    --package-path "$PKG_BUILD_DIR" \
    --resources "$PKG_BUILD_DIR" \
    "$BUILD_DIR/ReasoningCore-0.1.0-macos.pkg"

echo ""
echo "✅ Installer created successfully!"
echo "📦 Location: $BUILD_DIR/ReasoningCore-0.1.0-macos.pkg"
echo ""
echo "To test the installer:"
echo "  open $BUILD_DIR/ReasoningCore-0.1.0-macos.pkg"

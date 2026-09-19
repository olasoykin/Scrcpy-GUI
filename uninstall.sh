#!/usr/bin/env bash
# Uninstallation script for Scrcpy GUI

set -e

if [ "$EUID" -eq 0 ]; then
    INSTALL_PREFIX="/usr/local"
else
    INSTALL_PREFIX="$HOME/.local"
fi

BIN_DIR="$INSTALL_PREFIX/bin"
APP_DIR="$INSTALL_PREFIX/share/scrcpy-gui"
DESKTOP_DIR="$INSTALL_PREFIX/share/applications"
ICON_BASE="$INSTALL_PREFIX/share/icons/hicolor"
PIXMAPS_DIR="$INSTALL_PREFIX/share/pixmaps"

echo "==> Uninstalling Scrcpy GUI from $INSTALL_PREFIX..."

# Remove binaries and application files
rm -f "$BIN_DIR/scrcpy-gui"
rm -rf "$APP_DIR"

# Remove desktop entries
rm -f "$DESKTOP_DIR/com.github.scrcpy-gui.desktop"
rm -f "$DESKTOP_DIR/scrcpy-gui.desktop"

# Remove pixmaps
rm -f "$PIXMAPS_DIR/com.github.scrcpy-gui.svg"
rm -f "$PIXMAPS_DIR/com.github.scrcpy-gui.png"
rm -f "$PIXMAPS_DIR/scrcpy-gui.svg"
rm -f "$PIXMAPS_DIR/scrcpy-gui.png"

# Remove hicolor icons
if [ -d "$ICON_BASE" ]; then
    find "$ICON_BASE" -type f \( -name "com.github.scrcpy-gui.*" -o -name "scrcpy-gui.*" \) -delete 2>/dev/null || true
fi

# Remove pip package if installed
if command -v pip3 >/dev/null 2>&1; then
    pip3 uninstall -y scrcpy-gui >/dev/null 2>&1 || true
elif command -v pip >/dev/null 2>&1; then
    pip uninstall -y scrcpy-gui >/dev/null 2>&1 || true
fi

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
fi

if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t "$ICON_BASE" 2>/dev/null || true
fi

echo "==> Uninstallation completed successfully."

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
ICON_DIR="$INSTALL_PREFIX/share/icons/hicolor/scalable/apps"

echo "==> Uninstalling Scrcpy GUI from $INSTALL_PREFIX..."

rm -f "$BIN_DIR/scrcpy-gui"
rm -rf "$APP_DIR"
rm -f "$DESKTOP_DIR/com.github.scrcpy-gui.desktop"
rm -f "$ICON_DIR/com.github.scrcpy-gui.svg"

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
fi

echo "==> Uninstallation completed successfully."

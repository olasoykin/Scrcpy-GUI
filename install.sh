#!/usr/bin/env bash
# System installation script for Scrcpy GUI

set -e

SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"

if [ "$EUID" -eq 0 ]; then
    INSTALL_PREFIX="/usr/local"
    BIN_DIR="$INSTALL_PREFIX/bin"
    APP_DIR="$INSTALL_PREFIX/share/scrcpy-gui"
    DESKTOP_DIRS=("$INSTALL_PREFIX/share/applications")
    ICON_BASE="$INSTALL_PREFIX/share/icons/hicolor"
    PIXMAPS_DIR="$INSTALL_PREFIX/share/pixmaps"
    echo "==> Installing Scrcpy GUI system-wide ($INSTALL_PREFIX)..."
else
    INSTALL_PREFIX="$HOME/.local"
    BIN_DIR="$INSTALL_PREFIX/bin"
    APP_DIR="$INSTALL_PREFIX/share/scrcpy-gui"
    
    # Paths detected in XDG_DATA_DIRS (including Flatpak if present)
    DESKTOP_DIRS=("$HOME/.local/share/applications")
    if [ -d "$HOME/.local/share/flatpak/exports/share/applications" ]; then
        DESKTOP_DIRS+=("$HOME/.local/share/flatpak/exports/share/applications")
    fi
    
    ICON_BASE="$HOME/.local/share/icons/hicolor"
    PIXMAPS_DIR="$HOME/.local/share/pixmaps"
    echo "==> Installing Scrcpy GUI for current user ($HOME)..."
fi

echo "==> Searching for and removing previous versions..."

# Target files and directories to clean up before installing
CLEANUP_PATHS=(
    "$HOME/.local/share/scrcpy-gui"
    "$HOME/.local/bin/scrcpy-gui"
    "$HOME/.local/share/applications/com.github.scrcpy-gui.desktop"
    "$HOME/.local/share/applications/scrcpy-gui.desktop"
    "$HOME/.local/share/pixmaps/com.github.scrcpy-gui.svg"
    "$HOME/.local/share/pixmaps/com.github.scrcpy-gui.png"
    "$HOME/.local/share/pixmaps/scrcpy-gui.png"
    "$HOME/.local/share/pixmaps/scrcpy-gui.svg"
)

if [ "$EUID" -eq 0 ]; then
    CLEANUP_PATHS+=(
        "/usr/local/share/scrcpy-gui"
        "/usr/local/bin/scrcpy-gui"
        "/usr/local/share/applications/com.github.scrcpy-gui.desktop"
        "/usr/local/share/applications/scrcpy-gui.desktop"
        "/usr/local/share/pixmaps/com.github.scrcpy-gui.svg"
        "/usr/local/share/pixmaps/com.github.scrcpy-gui.png"
        "/usr/local/share/pixmaps/scrcpy-gui.png"
        "/usr/local/share/pixmaps/scrcpy-gui.svg"
        "/usr/share/scrcpy-gui"
        "/usr/bin/scrcpy-gui"
        "/usr/share/applications/com.github.scrcpy-gui.desktop"
        "/usr/share/applications/scrcpy-gui.desktop"
    )
fi

for cpath in "${CLEANUP_PATHS[@]}"; do
    if [ -e "$cpath" ] || [ -L "$cpath" ]; then
        echo "  - Removing old file/directory: $cpath"
        rm -rf "$cpath" 2>/dev/null || true
    fi
done

# Clean icons from hicolor directories
ICON_BASES=("$HOME/.local/share/icons/hicolor")
if [ "$EUID" -eq 0 ]; then
    ICON_BASES+=("/usr/local/share/icons/hicolor" "/usr/share/icons/hicolor")
fi

for ibase in "${ICON_BASES[@]}"; do
    if [ -d "$ibase" ]; then
        find "$ibase" -type f \( -name "com.github.scrcpy-gui.*" -o -name "scrcpy-gui.*" \) -delete 2>/dev/null || true
    fi
done

# Uninstall pip package if previously installed
if command -v pip3 >/dev/null 2>&1; then
    pip3 uninstall -y scrcpy-gui >/dev/null 2>&1 || true
elif command -v pip >/dev/null 2>&1; then
    pip uninstall -y scrcpy-gui >/dev/null 2>&1 || true
fi

# Create key directories
mkdir -p "$BIN_DIR"
mkdir -p "$APP_DIR"
mkdir -p "$PIXMAPS_DIR"

for ddir in "${DESKTOP_DIRS[@]}"; do
    mkdir -p "$ddir"
done

echo "==> Copying application files..."
cp -r "$SCRIPT_DIR/main.py" "$APP_DIR/"
cp -r "$SCRIPT_DIR/window.py" "$APP_DIR/"
if [ -f "$SCRIPT_DIR/qrcodegen.py" ]; then
    cp -r "$SCRIPT_DIR/qrcodegen.py" "$APP_DIR/"
fi
cp -r "$SCRIPT_DIR/pages" "$APP_DIR/"
if [ -d "$SCRIPT_DIR/assets" ]; then
    cp -r "$SCRIPT_DIR/assets" "$APP_DIR/"
fi

echo "==> Installing executable in $BIN_DIR/scrcpy-gui..."
cp "$SCRIPT_DIR/scrcpy-gui" "$BIN_DIR/scrcpy-gui"
chmod +x "$BIN_DIR/scrcpy-gui"

echo "==> Installing application icon (SVG and multisize PNG)..."
SCALABLE_DIR="$ICON_BASE/scalable/apps"
mkdir -p "$SCALABLE_DIR"

if [ -f "$SCRIPT_DIR/assets/com.github.scrcpy-gui.svg" ]; then
    cp "$SCRIPT_DIR/assets/com.github.scrcpy-gui.svg" "$SCALABLE_DIR/com.github.scrcpy-gui.svg"
    cp "$SCRIPT_DIR/assets/com.github.scrcpy-gui.svg" "$PIXMAPS_DIR/com.github.scrcpy-gui.svg"
fi

for s in 16 32 48 64 128 256 512; do
    if [ -f "$SCRIPT_DIR/assets/icon-${s}.png" ]; then
        SIZE_DIR="$ICON_BASE/${s}x${s}/apps"
        mkdir -p "$SIZE_DIR"
        cp "$SCRIPT_DIR/assets/icon-${s}.png" "$SIZE_DIR/com.github.scrcpy-gui.png"
    fi
done

if [ -f "$SCRIPT_DIR/assets/icon-256.png" ]; then
    cp "$SCRIPT_DIR/assets/icon-256.png" "$PIXMAPS_DIR/com.github.scrcpy-gui.png"
fi

# Generate .desktop file with exact absolute path to executable
DESKTOP_TMP=$(mktemp)
cat <<EOF > "$DESKTOP_TMP"
[Desktop Entry]
Version=1.0
Type=Application
Name=Scrcpy GUI
GenericName=Android Screen Mirroring
Comment=Graphical interface to mirror and control Android devices using scrcpy
Exec=$BIN_DIR/scrcpy-gui %U
Icon=com.github.scrcpy-gui
Terminal=false
Categories=Utility;RemoteAccess;GTK;
Keywords=scrcpy;android;mirror;adb;screen;adwaita;
StartupWMClass=com.github.scrcpy-gui
EOF

echo "==> Installing desktop shortcut (.desktop)..."
for ddir in "${DESKTOP_DIRS[@]}"; do
    cp "$DESKTOP_TMP" "$ddir/com.github.scrcpy-gui.desktop"
    chmod +x "$ddir/com.github.scrcpy-gui.desktop"
    touch "$ddir"
    if command -v update-desktop-database >/dev/null 2>&1; then
        update-desktop-database "$ddir" 2>/dev/null || true
    fi
done
rm -f "$DESKTOP_TMP"

if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t "$ICON_BASE" 2>/dev/null || true
fi

echo ""
echo "======================================================="
echo " Scrcpy GUI has been successfully installed! "
echo "======================================================="
echo "• Desktop shortcut has been created."
echo "• Main executable: $BIN_DIR/scrcpy-gui"
echo ""

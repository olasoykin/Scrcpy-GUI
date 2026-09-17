#!/usr/bin/env python3
"""Scrcpy GUI — A modern libadwaita interface for scrcpy."""

import sys

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from pathlib import Path
from gi.repository import Gtk, Adw, Gdk, Gio, GLib

from window import ScrcpyWindow

APP_ID = "com.github.scrcpy-gui"


class ScrcpyApp(Adw.Application):
    """Main application class."""

    def __init__(self):
        super().__init__(
            application_id=APP_ID,
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )
        self.connect("activate", self._on_activate)
        self.connect("startup", self._on_startup)

    def _on_startup(self, _app):
        """Load custom CSS and icon paths on startup."""
        display = Gdk.Display.get_default()
        if display:
            css_provider = Gtk.CssProvider()
            css_provider.load_from_string(CSS)
            Gtk.StyleContext.add_provider_for_display(
                display,
                css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
            )

            # Register icon search paths so GNOME Shell can find the app icon
            icon_theme = Gtk.IconTheme.get_for_display(display)
            assets_dir = str(Path(__file__).resolve().parent / "assets")
            icon_theme.add_search_path(assets_dir)

            user_icons = str(Path.home() / ".local" / "share" / "icons")
            icon_theme.add_search_path(user_icons)

    def _on_activate(self, _app):
        """Create and show the main window."""
        win = self.props.active_window
        if not win:
            win = ScrcpyWindow(application=self)
        win.present()


# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------

CSS = """
/* Sidebar styling */
stacksidebar list {
    background-color: alpha(@window_bg_color, 0.95);
}

stacksidebar row {
    padding: 8px 12px;
    margin: 2px 6px;
    border-radius: 8px;
}

stacksidebar row:selected {
    background-color: alpha(@accent_bg_color, 0.15);
    color: @accent_fg_color;
}

/* Command bar */
.monospace {
    font-family: "JetBrains Mono", "Fira Code", "Source Code Pro", monospace;
    font-size: 13px;
    padding: 4px 8px;
    background-color: alpha(@card_bg_color, 0.8);
    border-radius: 6px;
}

/* Start / Stop pill buttons */
.pill {
    padding-left: 16px;
    padding-right: 16px;
    border-radius: 999px;
    font-weight: 600;
}

/* Preferences group styling */
preferencesgroup {
    margin-top: 12px;
    margin-bottom: 4px;
}
"""


def main():
    GLib.set_prgname(APP_ID)
    GLib.set_application_name("Scrcpy GUI")
    app = ScrcpyApp()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())

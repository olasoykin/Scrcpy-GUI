import subprocess
import threading
from gi.repository import Gtk, Adw, GLib
from pages.base import BasePage

class AppsPage(BasePage):
    def __init__(self, on_changed=None):
        super().__init__(title="Apps", icon_name="view-grid-symbolic", on_changed=on_changed)
        self._packages = []
        self._build_ui()

    def _build_ui(self):
        # Group "App Launcher"
        grp_app = self._add_group("App Launcher")
        self.app_combo = self._add_combo(grp_app, "Select App", [("— Select installed app —", None)])
        
        refresh_btn = Gtk.Button(icon_name='view-refresh-symbolic', valign=Gtk.Align.CENTER)
        refresh_btn.add_css_class('flat')
        refresh_btn.set_tooltip_text('Refresh app list from device')
        refresh_btn.connect('clicked', self._refresh_apps)
        self.app_combo.add_suffix(refresh_btn)

        self.custom_app_entry = self._add_entry(
            grp_app, 
            "Custom Package Name"
        )

        # Group "Window"
        grp_window = self._add_group("Window")
        self.new_display_res = self._add_resolution(
            grp_window,
            "Resolution",
            subtitle="Virtual display width × height",
            width_placeholder="Width",
            height_placeholder="Height"
        )
        self.resizable = self._add_switch(
            grp_window,
            "Resizable",
            subtitle="Continuously resize the virtual display to match the window"
        )
        self.fullscreen = self._add_switch(
            grp_window,
            "Fullscreen",
            subtitle="Start in fullscreen mode"
        )

        # Group "Input"
        grp_input = self._add_group("Input")
        self.virtual_mouse = self._add_switch(
            grp_input,
            "Virtual Mouse",
            subtitle="Use UHID virtual mouse for better compatibility"
        )
        self.virtual_keyboard = self._add_switch(
            grp_input,
            "Virtual Keyboard",
            subtitle="Use UHID virtual keyboard for better compatibility"
        )

    def _refresh_apps(self, *args):
        """Run adb to list 3rd-party packages in background thread."""
        def _run():
            try:
                result = subprocess.run(
                    ['adb', 'shell', 'pm', 'list', 'packages', '-3'],
                    capture_output=True, text=True, timeout=15
                )
                packages = sorted(
                    line.removeprefix('package:').strip()
                    for line in result.stdout.splitlines()
                    if line.startswith('package:')
                )
            except Exception:
                packages = []
            GLib.idle_add(self._update_app_list, packages)
        threading.Thread(target=_run, daemon=True).start()

    def _update_app_list(self, packages):
        self._packages = packages
        options = [('— Select installed app —', None)] + [(p, p) for p in packages]
        self.app_combo._flag_options = options
        model = Gtk.StringList.new([name for name, _ in options])
        self.app_combo.set_model(model)
        self.app_combo.set_selected(0)
        return False  # Remove from idle

    def get_args(self) -> list[str]:
        args = []

        app_name = self._entry_val(self.custom_app_entry)
        if not app_name:
            app_name = self._combo_val(self.app_combo)

        if app_name:
            # When an app is selected, launch it in a new virtual display
            res = self._entry_val(self.new_display_res)
            if res:
                args.append(f'--new-display={res}')
            else:
                args.append('--new-display')

            args.append('--no-vd-system-decorations')
            args.append(f'--start-app={app_name}')

            if self.resizable.get_active(): args.append('--flex-display')
            if self.fullscreen.get_active(): args.append('--fullscreen')
            if self.virtual_mouse.get_active(): args.append('--mouse=uhid')
            if self.virtual_keyboard.get_active(): args.append('--keyboard=uhid')

        return args

    def reset(self):
        self.app_combo.set_selected(0)
        self.custom_app_entry.set_text('')
        self.new_display_res.set_text('')
        self.resizable.set_active(False)
        self.fullscreen.set_active(False)
        self.virtual_mouse.set_active(False)
        self.virtual_keyboard.set_active(False)

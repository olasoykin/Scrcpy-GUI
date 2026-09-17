import subprocess
import threading
from gi.repository import Gtk, Adw, GLib
from pages.base import BasePage

class AppsPage(BasePage):
    def __init__(self, on_changed=None):
        super().__init__(title="Apps", icon_name="view-grid-symbolic", on_changed=on_changed)
        self._build_ui()

    def _build_ui(self):
        # Group "Start Application"
        grp_app = self._add_group("Start Application")
        self.app_combo = self._add_combo(grp_app, "Start App", [("— Select app —", None)])
        
        refresh_btn = Gtk.Button(icon_name='view-refresh-symbolic', valign=Gtk.Align.CENTER)
        refresh_btn.add_css_class('flat')
        refresh_btn.set_tooltip_text('Refresh app list')
        refresh_btn.connect('clicked', self._refresh_apps)
        self.app_combo.add_suffix(refresh_btn)
        
        # Group "Virtual Display"
        grp_vd = self._add_group("Virtual Display")
        self.new_display = self._add_switch(grp_vd, "New Display", "Create a new virtual display")
        self.new_display_res = self._add_entry(grp_vd, "Resolution (e.g. 1920x1080)")
        self.new_display_dpi = self._add_entry(grp_vd, "DPI")
        self.flex_display = self._add_switch(grp_vd, "Flex Display", "Resize virtual display to match window")
        self.display_id = self._add_entry(grp_vd, "Display ID")
        self.no_vd_destroy_content = self._add_switch(grp_vd, "Keep Apps on Close", "Move apps to main display instead of destroying")
        self.no_vd_system_decorations = self._add_switch(grp_vd, "No System Decorations", "Disable virtual display system decorations")

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
        options = [('— Select app —', None)] + [(p, p) for p in packages]
        self.app_combo._flag_options = options
        model = Gtk.StringList.new([name for name, _ in options])
        self.app_combo.set_model(model)
        self.app_combo.set_selected(0)
        return False  # Remove from idle

    def get_args(self) -> list[str]:
        args = []
        val = self._combo_val(self.app_combo)
        if val: args.append(f'--start-app={val}')
        
        if self.new_display.get_active():
            res = self._entry_val(self.new_display_res)
            dpi = self._entry_val(self.new_display_dpi)
            if res and dpi:
                args.append(f'--new-display={res}/{dpi}')
            elif res:
                args.append(f'--new-display={res}')
            elif dpi:
                args.append(f'--new-display=/{dpi}')
            else:
                args.append('--new-display')
                
        if self.flex_display.get_active(): args.append('--flex-display')
        
        val = self._entry_val(self.display_id)
        if val: args.append(f'--display-id={val}')
        
        if self.no_vd_destroy_content.get_active(): args.append('--no-vd-destroy-content')
        if self.no_vd_system_decorations.get_active(): args.append('--no-vd-system-decorations')
        
        return args

    def reset(self):
        self.app_combo.set_selected(0)
        self.new_display.set_active(False)
        self.new_display_res.set_text('')
        self.new_display_dpi.set_text('')
        self.flex_display.set_active(False)
        self.display_id.set_text('')
        self.no_vd_destroy_content.set_active(False)
        self.no_vd_system_decorations.set_active(False)

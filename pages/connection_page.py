import subprocess
import threading

from gi.repository import Gtk, GLib

from pages.base import BasePage

class ConnectionPage(BasePage):
    def __init__(self, on_changed=None):
        super().__init__(title="Connection", icon_name="network-wired-symbolic", on_changed=on_changed)
        self._build_ui()

    def _build_ui(self):
        # Group: Device Selection
        grp_device = self._add_group("Device Selection")

        self.device_combo = self._add_combo(
            grp_device, "Connected Device",
            [("— Select device —", None)],
            subtitle="Devices currently seen by adb"
        )
        refresh_btn = Gtk.Button(icon_name="view-refresh-symbolic", valign=Gtk.Align.CENTER)
        refresh_btn.add_css_class("flat")
        refresh_btn.set_tooltip_text("Refresh device list")
        refresh_btn.connect("clicked", self._refresh_devices)
        self.device_combo.add_suffix(refresh_btn)
        # In addition to the generic _notify() wired up by _add_combo,
        # picking a device also fills in the Serial Number field below.
        self.device_combo.connect("notify::selected", self._on_device_selected)

        self.select_usb = self._add_switch(grp_device, "Select USB", subtitle="Use USB device (like adb -d)")
        self.select_tcpip = self._add_switch(grp_device, "Select TCP/IP", subtitle="Use TCP/IP device (like adb -e)")
        self.serial = self._add_entry(grp_device, "Serial Number")

        # Group: TCP/IP Connection
        grp_tcp = self._add_group("TCP/IP Connection")
        self.tcpip = self._add_entry(grp_tcp, "TCP/IP Address (ip[:port])")

        # Group: OTG
        grp_otg = self._add_group("OTG")
        self.otg = self._add_switch(grp_otg, "OTG Mode", subtitle="Simulate physical keyboard/mouse via OTG cable. No USB debugging needed.")

        # Populate the device list right away so it isn't empty on first view.
        self._refresh_devices()

    # ------------------------------------------------------------------
    # Device discovery
    # ------------------------------------------------------------------

    def _refresh_devices(self, *_args):
        """Run `adb devices` in a background thread to avoid blocking the UI."""
        def _run():
            devices = []
            try:
                result = subprocess.run(
                    ["adb", "devices", "-l"],
                    capture_output=True, text=True, timeout=10,
                )
                # First line is the header ("List of devices attached").
                for line in result.stdout.splitlines()[1:]:
                    parts = line.split()
                    if len(parts) >= 2 and parts[1] == "device":
                        devices.append(parts[0])
            except Exception:
                devices = []
            GLib.idle_add(self._update_device_list, devices)
        threading.Thread(target=_run, daemon=True).start()

    def _update_device_list(self, devices):
        options = [("— Select device —", None)] + [(d, d) for d in devices]
        self.device_combo._flag_options = options  # noqa: SLF001
        model = Gtk.StringList.new([name for name, _ in options])
        self.device_combo.set_model(model)
        self.device_combo.set_selected(0)
        return False  # remove from idle

    def _on_device_selected(self, combo, _pspec):
        serial = self._combo_val(combo)
        if serial:
            self.serial.set_text(serial)

    # ------------------------------------------------------------------
    # BasePage interface
    # ------------------------------------------------------------------

    def get_args(self) -> list[str]:
        args = []
        if self.select_usb.get_active():
            args.append('--select-usb')

        if self.select_tcpip.get_active():
            args.append('--select-tcpip')

        val = self._entry_val(self.serial)
        if val:
            args.append(f'--serial={val}')

        tcpip_val = self._entry_val(self.tcpip)
        if tcpip_val:
            args.append(f'--tcpip={tcpip_val}')

        if self.otg.get_active():
            args.append('--otg')

        return args

    def reset(self) -> None:
        self.device_combo.set_selected(0)
        self.select_usb.set_active(False)
        self.select_tcpip.set_active(False)
        self.serial.set_text('')
        self.tcpip.set_text('')
        self.otg.set_active(False)

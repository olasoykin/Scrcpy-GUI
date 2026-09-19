import subprocess
import threading

from gi.repository import Gtk, Adw, GLib

from pages.base import BasePage
from pages.qr_dialog import QrPairingDialog


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
        self.device_combo.connect("notify::selected", self._on_device_selected)

        self.select_usb = self._add_switch(grp_device, "Select USB", subtitle="Use USB device (like adb -d)")
        self.select_tcpip = self._add_switch(grp_device, "Select TCP/IP", subtitle="Use TCP/IP device (like adb -e)")

        # Make switches mutually exclusive with each other and serial entry
        self.select_usb.connect("notify::active", self._on_switch_toggled)
        self.select_tcpip.connect("notify::active", self._on_switch_toggled)

        self.serial = self._add_entry(grp_device, "Serial Number")

        # Group: Wireless Connection (ADB Inalámbrico)
        grp_wireless = self._add_group(
            "Wireless Connection (ADB)",
            description="Pair and connect Android 11+ devices via Wi-Fi without USB cables"
        )

        # Action Row: Pair via QR Code
        qr_row = Adw.ActionRow(
            title="Pair via QR Code",
            subtitle="Pair Android 11+ device by scanning QR code in Wireless Debugging"
        )
        qr_btn = Gtk.Button(
            label=" Pair via QR",
            icon_name="emblem-shared-symbolic",
            valign=Gtk.Align.CENTER
        )
        qr_btn.add_css_class("suggested-action")
        qr_btn.connect("clicked", self._open_qr_dialog)
        qr_row.add_suffix(qr_btn)
        grp_wireless.add(qr_row)

        # TCP/IP Connection entry
        self.tcpip = self._add_entry(grp_wireless, "TCP/IP Address (ip[:port])")

        connect_btn = Gtk.Button(
            label="Connect",
            icon_name="network-wireless-symbolic",
            valign=Gtk.Align.CENTER
        )
        connect_btn.connect("clicked", self._connect_tcpip)
        self.tcpip.add_suffix(connect_btn)

        # Group: OTG
        grp_otg = self._add_group("OTG")
        self.otg = self._add_switch(grp_otg, "OTG Mode", subtitle="Simulate physical keyboard/mouse via OTG cable. No USB debugging needed.")

        # Initial device list refresh
        self._refresh_devices()

    # ------------------------------------------------------------------
    # Switch handlers
    # ------------------------------------------------------------------

    def _on_switch_toggled(self, switch, _pspec):
        if not switch.get_active():
            return
        if switch == self.select_usb:
            self.select_tcpip.set_active(False)
        elif switch == self.select_tcpip:
            self.select_usb.set_active(False)

    # ------------------------------------------------------------------
    # Wireless Pairing Dialog
    # ------------------------------------------------------------------

    def _open_qr_dialog(self, _btn):
        parent_window = self.get_native()
        dialog = QrPairingDialog(parent_window, on_connected_cb=self._on_qr_connected)
        dialog.present()

    def _on_qr_connected(self, serial: str):
        def _apply():
            self.serial.set_text(serial)
            self.select_usb.set_active(False)
            self.select_tcpip.set_active(False)
        GLib.idle_add(_apply)
        self._refresh_devices()

    def _connect_tcpip(self, _btn):
        target = self._entry_val(self.tcpip)
        if not target:
            return

        def _run():
            try:
                subprocess.run(["adb", "connect", target], capture_output=True, text=True, timeout=8)
            except Exception:
                pass
            GLib.idle_add(lambda: self.serial.set_text(target))
            GLib.idle_add(self._refresh_devices)

        threading.Thread(target=_run, daemon=True).start()

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

        # Select the newly connected device if matching serial exists
        curr_serial = self._entry_val(self.serial)
        select_idx = 0
        if curr_serial:
            for i, (name, val) in enumerate(options):
                if val == curr_serial or (val and curr_serial in val):
                    select_idx = i
                    break

        self.device_combo.set_selected(select_idx)
        return False

    def _on_device_selected(self, combo, _pspec):
        serial = self._combo_val(combo)
        if serial:
            self.serial.set_text(serial)
            self.select_usb.set_active(False)
            self.select_tcpip.set_active(False)

    # ------------------------------------------------------------------
    # BasePage interface
    # ------------------------------------------------------------------

    def get_args(self) -> list[str]:
        args = []

        # Scrcpy ONLY allows at most ONE device selector flag among:
        # --serial=<serial>, --select-usb, --select-tcpip, or --tcpip=<addr>
        val = self._entry_val(self.serial)
        if val:
            args.append(f'--serial={val}')
        elif self.select_usb.get_active():
            args.append('--select-usb')
        elif self.select_tcpip.get_active():
            args.append('--select-tcpip')
        else:
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

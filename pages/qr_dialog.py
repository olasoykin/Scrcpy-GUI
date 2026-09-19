"""ADB Wireless QR Pairing Dialog for Scrcpy-GUI."""

import random
import re
import subprocess
import threading
import time

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gdk, GLib
import cairo
from qrcodegen import QrCode


def generate_qr_texture(text: str, size_px: int = 240) -> Gdk.Texture:
    """Generate a Gdk.Texture containing a high-contrast QR code image."""
    qr = QrCode.encode_text(text, QrCode.Ecc.MEDIUM)
    size = qr.get_size()
    border = 2
    total_modules = size + border * 2
    scale = size_px / total_modules
    actual_img_size = int(total_modules * scale)

    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, actual_img_size, actual_img_size)
    ctx = cairo.Context(surface)

    # Background: White
    ctx.set_source_rgb(1.0, 1.0, 1.0)
    ctx.paint()

    # Modules: Dark (#111111)
    ctx.set_source_rgb(0.07, 0.07, 0.07)
    for y in range(size):
        for x in range(size):
            if qr.get_module(x, y):
                ctx.rectangle(
                    (x + border) * scale,
                    (y + border) * scale,
                    scale + 0.4,
                    scale + 0.4,
                )
                ctx.fill()

    data = surface.get_data()
    bytes_data = GLib.Bytes.new(data.tobytes())
    return Gdk.MemoryTexture.new(
        actual_img_size,
        actual_img_size,
        Gdk.MemoryFormat.B8G8R8A8_PREMULTIPLIED,
        bytes_data,
        surface.get_stride(),
    )


class QrPairingDialog(Gtk.Window):
    """Modal dialog for ADB Wireless QR pairing and manual code pairing."""

    def __init__(self, parent_window, on_connected_cb=None):
        super().__init__(
            title="Wireless ADB Connection",
            transient_for=parent_window,
            modal=True,
            default_width=440,
            default_height=600,
            resizable=False,
        )
        self.on_connected_cb = on_connected_cb
        self._listening = True

        # Generate unique random pairing credentials for this session
        self.pairing_code = f"{random.randint(100000, 999999)}"
        self.service_name = f"scrcpy-gui-{random.randint(1000, 9999)}"
        self.qr_payload = f"WIFI:T:ADB;S:{self.service_name};P:{self.pairing_code};;"

        self._build_ui()
        self.connect("close-request", self._on_close_request)

        # Start mDNS background listener
        self._listener_thread = threading.Thread(
            target=_listen_for_qr_pairing,
            args=(self.service_name, self.pairing_code, self._update_status, self._on_success, self._is_listening),
            daemon=True,
        )
        self._listener_thread.start()

    def _is_listening(self) -> bool:
        return self._listening

    def _on_close_request(self, *_args):
        self._listening = False
        return False

    def _build_ui(self):
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_child(root)

        # HeaderBar
        header = Adw.HeaderBar()
        header.set_title_widget(Gtk.Label(label="ADB QR Connection", css_classes=["title"]))
        close_btn = Gtk.Button(label="Close")
        close_btn.connect("clicked", lambda _: self.close())
        header.pack_end(close_btn)
        root.append(header)

        # Main scrollable view
        scroller = Gtk.ScrolledWindow(vexpand=True, hexpand=True)
        root.append(scroller)

        container = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=16,
            margin_top=16,
            margin_bottom=20,
            margin_start=24,
            margin_end=24,
        )
        scroller.set_child(container)

        # View Stack (QR View vs Manual Code View)
        self.stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        container.append(self.stack)

        # -------------------------------------------------------------
        # View 1: QR Code View
        # -------------------------------------------------------------
        qr_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)

        inst_label = Gtk.Label(
            label="<b>1. Connect your phone to the same Wi-Fi network.</b>\n"
                  "<b>2. On your phone go to:</b>\n"
                  "<i>Settings > Developer options > Wireless debugging > Pair device with QR code</i>\n"
                  "<b>3. Scan the following code:</b>",
            use_markup=True,
            wrap=True,
            justify=Gtk.Justification.LEFT,
        )
        inst_label.add_css_class("dim-label")
        qr_box.append(inst_label)

        # QR Code Display Frame
        qr_frame = Gtk.Frame(halign=Gtk.Align.CENTER)
        qr_frame.add_css_class("card")
        qr_texture = generate_qr_texture(self.qr_payload, size_px=230)
        qr_picture = Gtk.Picture.new_for_paintable(qr_texture)
        qr_picture.set_size_request(230, 230)
        qr_picture.set_margin_top(12)
        qr_picture.set_margin_bottom(12)
        qr_picture.set_margin_start(12)
        qr_picture.set_margin_end(12)
        qr_frame.set_child(qr_picture)
        qr_box.append(qr_frame)

        # Session info
        info_label = Gtk.Label(
            label=f"Service: <b>{self.service_name}</b>  |  PIN: <b>{self.pairing_code}</b>",
            use_markup=True,
            halign=Gtk.Align.CENTER,
        )
        info_label.add_css_class("dim-label")
        info_label.add_css_class("caption")
        qr_box.append(info_label)

        # Status indicator box
        self.status_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=10,
            halign=Gtk.Align.CENTER,
            margin_top=4,
        )
        self.spinner = Gtk.Spinner(spinning=True)
        self.status_box.append(self.spinner)

        self.status_label = Gtk.Label(
            label="Searching for device on Wi-Fi network...",
            wrap=True,
            halign=Gtk.Align.CENTER,
        )
        self.status_box.append(self.status_label)
        qr_box.append(self.status_box)

        # Switch to Manual Code view button
        switch_to_manual_btn = Gtk.Button(
            label="Pair using 6-digit code...",
            halign=Gtk.Align.CENTER,
            margin_top=8,
        )
        switch_to_manual_btn.add_css_class("flat")
        switch_to_manual_btn.connect("clicked", lambda _: self.stack.set_visible_child_name("manual"))
        qr_box.append(switch_to_manual_btn)

        self.stack.add_named(qr_box, "qr")

        # -------------------------------------------------------------
        # View 2: Manual Pairing Code View
        # -------------------------------------------------------------
        manual_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)

        manual_inst = Gtk.Label(
            label="<b>Pair using 6-digit pairing code</b>\n"
                  "On your device go to: <i>Wireless debugging > Pair device with pairing code</i>.",
            use_markup=True,
            wrap=True,
        )
        manual_inst.add_css_class("dim-label")
        manual_box.append(manual_inst)

        group = Adw.PreferencesGroup()
        self.manual_ip_entry = Adw.EntryRow(title="Pairing IP & Port (e.g. 192.168.1.50:37123)")
        self.manual_code_entry = Adw.EntryRow(title="Pairing Code (6 digits)")
        group.add(self.manual_ip_entry)
        group.add(self.manual_code_entry)
        manual_box.append(group)

        self.manual_pair_btn = Gtk.Button(
            label="Pair Device",
            halign=Gtk.Align.CENTER,
        )
        self.manual_pair_btn.add_css_class("suggested-action")
        self.manual_pair_btn.connect("clicked", self._on_manual_pair_clicked)
        manual_box.append(self.manual_pair_btn)

        self.manual_status_label = Gtk.Label(
            label="",
            wrap=True,
            halign=Gtk.Align.CENTER,
        )
        manual_box.append(self.manual_status_label)

        switch_to_qr_btn = Gtk.Button(
            label="Back to QR code",
            halign=Gtk.Align.CENTER,
            margin_top=8,
        )
        switch_to_qr_btn.add_css_class("flat")
        switch_to_qr_btn.connect("clicked", lambda _: self.stack.set_visible_child_name("qr"))
        manual_box.append(switch_to_qr_btn)

        self.stack.add_named(manual_box, "manual")
        self.stack.set_visible_child_name("qr")

    def _update_status(self, text: str, is_error: bool = False, is_done: bool = False):
        def _update():
            self.status_label.set_text(text)
            if is_done or is_error:
                self.spinner.stop()
                self.spinner.set_visible(False)
            else:
                self.spinner.set_visible(True)
                self.spinner.start()
        GLib.idle_add(_update)

    def _on_success(self, serial: str):
        def _done():
            self.status_label.set_markup(f"<b>Successfully connected to {serial}!</b>")
            self.spinner.stop()
            self.spinner.set_visible(False)
            if self.on_connected_cb:
                self.on_connected_cb(serial)
            GLib.timeout_add(1500, self.close)
        GLib.idle_add(_done)

    def _on_manual_pair_clicked(self, _btn):
        ip_port = self.manual_ip_entry.get_text().strip()
        code = self.manual_code_entry.get_text().strip()
        if not ip_port or not code:
            self.manual_status_label.set_text("Please enter the IP:Port and pairing code.")
            return

        self.manual_pair_btn.set_sensitive(False)
        self.manual_status_label.set_text("Pairing...")

        def _worker():
            ip = ip_port.split(":")[0] if ":" in ip_port else ip_port
            try:
                res = subprocess.run(
                    ["adb", "pair", ip_port, code],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if "Successfully paired" in res.stdout or res.returncode == 0:
                    GLib.idle_add(lambda: self.manual_status_label.set_text("Paired. Connecting..."))
                    # Discover connect port or attempt adb connect
                    conn_serial = _connect_after_pairing(ip)
                    if conn_serial:
                        GLib.idle_add(lambda: self.manual_status_label.set_markup(f"<b>Connected to {conn_serial}!</b>"))
                        if self.on_connected_cb:
                            GLib.idle_add(lambda: self.on_connected_cb(conn_serial))
                        GLib.timeout_add(1500, self.close)
                        return
                    else:
                        GLib.idle_add(lambda: self.manual_status_label.set_text("Paired, but could not auto-connect. Try connecting with IP directly."))
                else:
                    err_msg = res.stderr.strip() or res.stdout.strip() or "Pairing error."
                    GLib.idle_add(lambda: self.manual_status_label.set_text(f"Error: {err_msg}"))
            except Exception as e:
                GLib.idle_add(lambda: self.manual_status_label.set_text(f"Error: {e}"))
            finally:
                GLib.idle_add(lambda: self.manual_pair_btn.set_sensitive(True))

        threading.Thread(target=_worker, daemon=True).start()


def _listen_for_qr_pairing(service_name, pairing_code, status_cb, success_cb, is_listening_fn):
    """Background loop polling `adb mdns services` to detect QR scanning and auto-pair."""
    paired_ip = None
    pairing_attempts = 0

    while is_listening_fn() and pairing_attempts < 120:  # ~2 minutes timeout
        time.sleep(1.0)
        if not is_listening_fn():
            break

        try:
            res = subprocess.run(
                ["adb", "mdns", "services"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            stdout = res.stdout or ""
        except Exception:
            continue

        # Look for _adb-tls-pairing in mdns output
        target_pair = None
        for line in stdout.splitlines():
            if "_adb-tls-pairing" in line:
                m = re.search(r'(\d{1,3}(?:\.\d{1,3}){3})[:\s]+(\d+)', line)
                if m:
                    target_pair = (m.group(1), m.group(2))
                    break

        if target_pair:
            ip, port = target_pair
            status_cb(f"Device detected ({ip}:{port}). Pairing...")

            # Run adb pair
            try:
                pair_res = subprocess.run(
                    ["adb", "pair", f"{ip}:{port}", pairing_code],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if "Successfully paired" in pair_res.stdout or pair_res.returncode == 0:
                    status_cb("Pairing successful. Establishing ADB connection...")
                    paired_ip = ip
                    break
                else:
                    status_cb(f"Pairing failed: {pair_res.stderr.strip() or pair_res.stdout.strip()}", is_error=True)
            except Exception as e:
                status_cb(f"Error during pairing: {e}", is_error=True)

    if paired_ip and is_listening_fn():
        # Connect to the paired device
        conn_serial = _connect_after_pairing(paired_ip)
        if conn_serial:
            success_cb(conn_serial)
        else:
            status_cb("Paired, but connection port not detected. Try connecting manually.", is_error=True)
    elif not paired_ip and is_listening_fn():
        status_cb("Timed out. Make sure to scan QR from Wireless Debugging screen.", is_done=True)


def _connect_after_pairing(ip: str) -> str | None:
    """Helper to locate `_adb-tls-connect` port and run `adb connect`."""
    connect_port = None
    for _ in range(10): # try for ~5 seconds
        time.sleep(0.5)
        try:
            res = subprocess.run(
                ["adb", "mdns", "services"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            for line in res.stdout.splitlines():
                if "_adb-tls-connect" in line and ip in line:
                    m = re.search(r'(\d{1,3}(?:\.\d{1,3}){3})[:\s]+(\d+)', line)
                    if m:
                        connect_port = m.group(2)
                        break
            if connect_port:
                break
        except Exception:
            pass

    ports_to_try = [connect_port, "5555"] if connect_port else ["5555"]
    for p in ports_to_try:
        if not p:
            continue
        target = f"{ip}:{p}"
        try:
            conn_res = subprocess.run(
                ["adb", "connect", target],
                capture_output=True,
                text=True,
                timeout=8,
            )
            if "connected to" in conn_res.stdout.lower():
                return target
        except Exception:
            pass

    # Fallback check adb devices to see if ip is already listed
    try:
        dev_res = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=5)
        for line in dev_res.stdout.splitlines():
            if ip in line and "device" in line:
                return line.split()[0]
    except Exception:
        pass

    return None

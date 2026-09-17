"""Main application window with sidebar navigation and command bar."""

import shlex
import shutil
import subprocess
import threading

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gdk, GLib

from pages import (
    DisplayPage,
    AudioPage,
    ControlPage,
    ConnectionPage,
    RecordingPage,
    CameraPage,
    AppsPage,
    AdvancedPage,
)


class ScrcpyWindow(Adw.ApplicationWindow):
    """The main window for Scrcpy GUI."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("Scrcpy GUI")
        self.set_icon_name("com.github.scrcpy-gui")
        self.set_default_size(920, 700)
        self._process = None
        # True while a stop was requested by the user, so we don't treat
        # the resulting process exit (e.g. from terminate()) as an error.
        self._stopping = False

        self._build_ui()
        self._update_command()
        self.connect("close-request", self._on_close_request)
        self._check_scrcpy_available()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        # Root layout: vertical box
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(root)

        # Header bar
        header = Adw.HeaderBar()
        header.set_title_widget(Gtk.Label(label="Scrcpy GUI", css_classes=["title"]))
        root.append(header)

        # Main content: sidebar + stack
        content_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, vexpand=True)
        root.append(content_box)

        # Stack for pages
        self._stack = Gtk.Stack()
        self._stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self._stack.set_transition_duration(200)

        # Sidebar
        sidebar = Gtk.StackSidebar()
        sidebar.set_stack(self._stack)
        sidebar.set_size_request(200, -1)
        content_box.append(sidebar)

        # Separator between sidebar and content
        sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        content_box.append(sep)

        # Add stack to content (let it expand)
        self._stack.set_hexpand(True)
        self._stack.set_vexpand(True)
        content_box.append(self._stack)

        # Create all pages
        self._pages = []
        self._create_pages()

        # Bottom command bar
        self._build_command_bar(root)

    def _create_pages(self):
        """Instantiate all settings pages and add them to the stack."""
        page_classes = [
            ("display", DisplayPage),
            ("audio", AudioPage),
            ("control", ControlPage),
            ("connection", ConnectionPage),
            ("recording", RecordingPage),
            ("camera", CameraPage),
            ("apps", AppsPage),
            ("advanced", AdvancedPage),
        ]

        for name, cls in page_classes:
            page = cls(on_changed=self._update_command)
            self._pages.append(page)

            # Wrap in a ScrolledWindow for proper scrolling
            scroll = Gtk.ScrolledWindow(
                hscrollbar_policy=Gtk.PolicyType.NEVER,
                vscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
                vexpand=True,
                hexpand=True,
            )

            # Use Adw.Clamp to limit content width
            clamp = Adw.Clamp(maximum_size=800, tightening_threshold=600)
            clamp.set_child(page)
            scroll.set_child(clamp)

            self._stack.add_titled(scroll, name, page.get_title())

    def _build_command_bar(self, root: Gtk.Box):
        """Build the bottom bar with command preview and action buttons."""
        # Separator above command bar
        root.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        bar = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=8,
            margin_start=12,
            margin_end=12,
            margin_top=8,
            margin_bottom=8,
        )
        root.append(bar)

        # Command label
        cmd_icon = Gtk.Image(icon_name="utilities-terminal-symbolic")
        bar.append(cmd_icon)

        # Scrolled command preview
        scroll = Gtk.ScrolledWindow(
            hscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
            vscrollbar_policy=Gtk.PolicyType.NEVER,
            hexpand=True,
        )
        scroll.set_max_content_height(32)

        self._cmd_label = Gtk.Label(
            label="scrcpy",
            xalign=0.0,
            selectable=True,
            css_classes=["monospace"],
            wrap=False,
            single_line_mode=True,
        )
        scroll.set_child(self._cmd_label)
        bar.append(scroll)

        # Copy button
        copy_btn = Gtk.Button(icon_name="edit-copy-symbolic", tooltip_text="Copy command")
        copy_btn.add_css_class("flat")
        copy_btn.connect("clicked", self._on_copy)
        bar.append(copy_btn)

        # Reset button
        reset_btn = Gtk.Button(icon_name="edit-clear-all-symbolic", tooltip_text="Reset all settings")
        reset_btn.add_css_class("flat")
        reset_btn.connect("clicked", self._on_reset)
        bar.append(reset_btn)

        # Start button
        self._start_btn = Gtk.Button(label="Start")
        self._start_btn.add_css_class("suggested-action")
        self._start_btn.add_css_class("pill")
        start_content = Adw.ButtonContent(
            icon_name="media-playback-start-symbolic", label="Start"
        )
        self._start_btn.set_child(start_content)
        self._start_btn.connect("clicked", self._on_start)
        bar.append(self._start_btn)

        # Stop button (hidden by default)
        self._stop_btn = Gtk.Button(label="Stop")
        self._stop_btn.add_css_class("destructive-action")
        self._stop_btn.add_css_class("pill")
        stop_content = Adw.ButtonContent(
            icon_name="media-playback-stop-symbolic", label="Stop"
        )
        self._stop_btn.set_child(stop_content)
        self._stop_btn.connect("clicked", self._on_stop)
        self._stop_btn.set_visible(False)
        bar.append(self._stop_btn)

    # ------------------------------------------------------------------
    # Command building
    # ------------------------------------------------------------------

    def _build_command(self) -> list[str]:
        """Collect args from all pages and return the full command."""
        cmd = ["scrcpy"]
        for page in self._pages:
            cmd.extend(page.get_args())
        return cmd

    def _update_command(self):
        """Refresh the command preview label.

        The command is actually executed as an argument list (see
        ``_on_start``), so spaces inside a single argument (a window
        title, a file path...) are never a problem at runtime. But the
        *preview* is plain text meant to be read and copy-pasted into a
        real shell, so it needs proper shell quoting or a copy-pasted
        command with, say, a window title containing spaces would be
        silently split into several arguments.
        """
        cmd = self._build_command()
        self._cmd_label.set_text(shlex.join(cmd))

    # ------------------------------------------------------------------
    # Startup checks
    # ------------------------------------------------------------------

    def _check_scrcpy_available(self):
        """Warn early if scrcpy (or adb) isn't on PATH.

        Without this, the first sign of trouble was a generic error only
        after the user pressed Start.
        """
        missing = [name for name in ("scrcpy", "adb") if shutil.which(name) is None]
        if missing:
            GLib.idle_add(
                self._show_toast,
                Adw.Toast(
                    title=f"{' and '.join(missing)} not found on PATH — install before starting",
                    timeout=6,
                ),
            )

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _on_copy(self, _btn):
        """Copy the current command to the clipboard."""
        cmd_text = self._cmd_label.get_text()
        clipboard = self.get_clipboard()
        clipboard.set(cmd_text)
        # Show a toast
        toast = Adw.Toast(title="Command copied to clipboard")
        toast.set_timeout(2)
        # We need a ToastOverlay — let's find or add one
        self._show_toast(toast)

    def _show_toast(self, toast: Adw.Toast):
        """Show a toast notification. Wraps content in a ToastOverlay if needed."""
        # Walk up to find a ToastOverlay, or wrap our content
        if not hasattr(self, "_toast_overlay"):
            # Re-wrap our content in a ToastOverlay
            current_content = self.get_content()
            self._toast_overlay = Adw.ToastOverlay()
            self.set_content(self._toast_overlay)
            self._toast_overlay.set_child(current_content)
        self._toast_overlay.add_toast(toast)
        return False  # safe to use directly as a GLib.idle_add callback

    def _show_error_dialog(self, heading: str, body: str):
        """Show scrcpy's own error output, instead of swallowing it."""
        dialog = Adw.MessageDialog(
            transient_for=self,
            heading=heading,
            body=body or "scrcpy exited unexpectedly, with no further output.",
        )
        dialog.add_response("close", "Close")
        dialog.set_default_response("close")
        dialog.set_close_response("close")
        dialog.present()

    def _on_reset(self, _btn):
        """Reset all pages to default values."""
        for page in self._pages:
            page.reset()
        self._update_command()

    def _on_start(self, _btn):
        """Launch scrcpy with the built command."""
        if self._process is not None:
            # Already running — the Start button should be hidden in this
            # state, but guard against a stray double-click regardless.
            return

        cmd = self._build_command()
        try:
            self._process = subprocess.Popen(
                cmd,
                stderr=subprocess.PIPE,
                text=True,
            )
        except FileNotFoundError:
            self._show_toast(Adw.Toast(title="scrcpy not found. Please install scrcpy."))
            return
        except Exception as e:
            self._show_toast(Adw.Toast(title=f"Error: {e}"))
            return

        self._start_btn.set_visible(False)
        self._stop_btn.set_visible(True)
        # Monitor process in a thread
        thread = threading.Thread(target=self._monitor_process, daemon=True)
        thread.start()

    def _monitor_process(self):
        """Wait for the scrcpy process to exit and collect its stderr."""
        process = self._process
        if process is None:
            return
        # communicate() blocks until the process exits (like wait()) and
        # also drains stderr, so we can surface real failures — e.g. an
        # unauthorized device, or an unsupported combination of flags —
        # instead of just noticing that the process is gone.
        _, stderr = process.communicate()
        GLib.idle_add(self._on_process_exited, process.returncode, stderr or "")

    def _on_process_exited(self, returncode=0, stderr=""):
        """Called on main thread when scrcpy exits."""
        self._process = None
        self._start_btn.set_visible(True)
        self._stop_btn.set_visible(False)

        was_stopping, self._stopping = self._stopping, False
        # A non-zero exit from a user-requested stop (e.g. SIGTERM) isn't
        # a failure worth interrupting the user about.
        if not was_stopping and returncode not in (0, None):
            self._show_error_dialog(
                f"scrcpy exited with code {returncode}", stderr.strip()
            )
        return False

    def _on_stop(self, _btn):
        """Terminate the running scrcpy process."""
        if self._process:
            self._stopping = True
            self._process.terminate()

    def _on_close_request(self, *_args):
        """Make sure we don't leave an orphaned scrcpy process running
        in the background after the window is closed."""
        if self._process:
            try:
                self._process.terminate()
            except Exception:
                pass
        return False  # allow the window to close

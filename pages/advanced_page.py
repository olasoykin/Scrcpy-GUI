from pages.base import BasePage

class AdvancedPage(BasePage):
    def __init__(self, on_changed=None):
        super().__init__(title="Advanced", icon_name="preferences-other-symbolic", on_changed=on_changed)
        self._build_ui()

    def _build_ui(self):
        # Group "V4L2 (Linux)"
        grp_v4l2 = self._add_group("V4L2 (Linux)")
        self.v4l2_sink = self._add_entry(grp_v4l2, "V4L2 Sink (/dev/videoN)")
        self.v4l2_buffer = self._add_entry(grp_v4l2, "V4L2 Buffer (ms)")

        # Group "Buffering"
        grp_buf = self._add_group("Buffering")
        self.video_buffer = self._add_entry(grp_buf, "Video Buffer (ms)")

        # Group "File Transfer"
        grp_push = self._add_group("File Transfer")
        self.push_target = self._add_entry(grp_push, "Push Target Path")

        # Group "Shortcuts"
        grp_shortcut = self._add_group("Shortcuts")
        self.shortcut_mod = self._add_entry(grp_shortcut, "Shortcut Modifier")

        # Group "Miscellaneous"
        grp_misc = self._add_group("Miscellaneous")
        self.print_fps = self._add_switch(grp_misc, "Print FPS", "Show framerate in console")
        self.no_cleanup = self._add_switch(grp_misc, "No Cleanup", "Don't restore device state on exit")
        self.no_video = self._add_switch(grp_misc, "No Video", "Disable video forwarding")
        self.kill_adb_on_close = self._add_switch(grp_misc, "Kill ADB on Close", "Kill adb when scrcpy exits")
        self.force_adb_forward = self._add_switch(grp_misc, "Force ADB Forward", "Don't use adb reverse")
        self.no_downsize_on_error = self._add_switch(grp_misc, "No Downsize on Error", "Don't retry with lower resolution on error")
        self.render_driver = self._add_combo(grp_misc, "Render Driver", [
            ("Auto", None),
            ("OpenGL", "opengl"),
            ("OpenGL ES 2", "opengles2"),
            ("OpenGL ES", "opengles"),
            ("Software", "software")
        ])

    def get_args(self) -> list[str]:
        args = []
        val = self._entry_val(self.v4l2_sink)
        if val: args.append(f'--v4l2-sink={val}')
        
        val = self._entry_val(self.v4l2_buffer)
        if val: args.append(f'--v4l2-buffer={val}')
        
        val = self._entry_val(self.video_buffer)
        if val: args.append(f'--video-buffer={val}')
        
        val = self._entry_val(self.push_target)
        if val: args.append(f'--push-target={val}')
        
        val = self._entry_val(self.shortcut_mod)
        if val: args.append(f'--shortcut-mod={val}')
        
        if self.print_fps.get_active(): args.append('--print-fps')
        if self.no_cleanup.get_active(): args.append('--no-cleanup')
        if self.no_video.get_active(): args.append('--no-video')
        if self.kill_adb_on_close.get_active(): args.append('--kill-adb-on-close')
        if self.force_adb_forward.get_active(): args.append('--force-adb-forward')
        if self.no_downsize_on_error.get_active(): args.append('--no-downsize-on-error')
        
        val = self._combo_val(self.render_driver)
        if val: args.append(f'--render-driver={val}')
        
        return args

    def reset(self):
        self.v4l2_sink.set_text('')
        self.v4l2_buffer.set_text('')
        self.video_buffer.set_text('')
        self.push_target.set_text('')
        self.shortcut_mod.set_text('')
        self.print_fps.set_active(False)
        self.no_cleanup.set_active(False)
        self.no_video.set_active(False)
        self.kill_adb_on_close.set_active(False)
        self.force_adb_forward.set_active(False)
        self.no_downsize_on_error.set_active(False)
        self.render_driver.set_selected(0)

from pages.base import BasePage

class ControlPage(BasePage):
    def __init__(self, on_changed=None):
        super().__init__(title="Control", icon_name="input-keyboard-symbolic", on_changed=on_changed)
        self._build_ui()

    def _build_ui(self):
        # Group: Input Modes
        grp_input = self._add_group("Input Modes")
        self.keyboard_mode = self._add_combo(
            grp_input, "Keyboard Mode",
            [("Default (sdk)", None), ("Disabled", "disabled"), ("UHID", "uhid"), ("AOA", "aoa")],
            subtitle="How keyboard inputs are sent"
        )
        self.mouse_mode = self._add_combo(
            grp_input, "Mouse Mode",
            [("Default (sdk)", None), ("Disabled", "disabled"), ("UHID", "uhid"), ("AOA", "aoa")],
            subtitle="How mouse inputs are sent"
        )
        self.gamepad_mode = self._add_combo(
            grp_input, "Gamepad Mode",
            [("Default (disabled)", None), ("UHID", "uhid"), ("AOA", "aoa")],
            subtitle="How gamepad inputs are sent"
        )

        # Group: Touch & Display
        grp_touch = self._add_group("Touch and Display")
        self.show_touches = self._add_switch(grp_touch, "Show Touches", subtitle="Show physical touches on screen")
        self.stay_awake = self._add_switch(grp_touch, "Stay Awake", subtitle="Keep device on while plugged in")
        self.keep_active = self._add_switch(grp_touch, "Keep Active", subtitle="Simulate user activity to keep screen on")
        self.turn_screen_off = self._add_switch(grp_touch, "Turn Screen Off", subtitle="Turn device screen off immediately")
        self.power_off_on_close = self._add_switch(grp_touch, "Power Off on Close", subtitle="Turn screen off when closing scrcpy")
        self.no_power_on = self._add_switch(grp_touch, "No Power On", subtitle="Don't power on device on start")
        self.screen_off_timeout = self._add_entry(grp_touch, "Screen Off Timeout (seconds)")
        self.disable_screensaver = self._add_switch(grp_touch, "Disable Screensaver", subtitle="Disable screensaver while running")

        # Group: Keyboard & Clipboard
        grp_kb = self._add_group("Keyboard and Clipboard")
        self.no_control = self._add_switch(grp_kb, "No Control", subtitle="Mirror only, no input (read-only)")
        self.no_key_repeat = self._add_switch(grp_kb, "No Key Repeat", subtitle="Don't forward repeated key events")
        self.no_mouse_hover = self._add_switch(grp_kb, "No Mouse Hover", subtitle="Don't forward mouse hover events")
        self.prefer_text = self._add_switch(grp_kb, "Prefer Text", subtitle="Inject alpha chars as text events")
        self.legacy_paste = self._add_switch(grp_kb, "Legacy Paste", subtitle="Paste as key events on Ctrl+V")
        self.no_clipboard_autosync = self._add_switch(grp_kb, "No Clipboard Autosync", subtitle="Disable automatic clipboard sync")

    def get_args(self) -> list[str]:
        args = []
        
        val = self._combo_val(self.keyboard_mode)
        if val: args.append(f'--keyboard={val}')
        val = self._combo_val(self.mouse_mode)
        if val: args.append(f'--mouse={val}')
        val = self._combo_val(self.gamepad_mode)
        if val: args.append(f'--gamepad={val}')
        
        if self.show_touches.get_active(): args.append('--show-touches')
        if self.stay_awake.get_active(): args.append('--stay-awake')
        if self.keep_active.get_active(): args.append('--keep-active')
        if self.turn_screen_off.get_active(): args.append('--turn-screen-off')
        if self.power_off_on_close.get_active(): args.append('--power-off-on-close')
        if self.no_power_on.get_active(): args.append('--no-power-on')
        
        val = self._entry_val(self.screen_off_timeout)
        if val: args.append(f'--screen-off-timeout={val}')
        
        if self.disable_screensaver.get_active(): args.append('--disable-screensaver')
        
        if self.no_control.get_active(): args.append('--no-control')
        if self.no_key_repeat.get_active(): args.append('--no-key-repeat')
        if self.no_mouse_hover.get_active(): args.append('--no-mouse-hover')
        if self.prefer_text.get_active(): args.append('--prefer-text')
        if self.legacy_paste.get_active(): args.append('--legacy-paste')
        if self.no_clipboard_autosync.get_active(): args.append('--no-clipboard-autosync')

        return args

    def reset(self) -> None:
        self.keyboard_mode.set_selected(0)
        self.mouse_mode.set_selected(0)
        self.gamepad_mode.set_selected(0)
        
        self.show_touches.set_active(False)
        self.stay_awake.set_active(False)
        self.keep_active.set_active(False)
        self.turn_screen_off.set_active(False)
        self.power_off_on_close.set_active(False)
        self.no_power_on.set_active(False)
        self.screen_off_timeout.set_text('')
        self.disable_screensaver.set_active(False)
        
        self.no_control.set_active(False)
        self.no_key_repeat.set_active(False)
        self.no_mouse_hover.set_active(False)
        self.prefer_text.set_active(False)
        self.legacy_paste.set_active(False)
        self.no_clipboard_autosync.set_active(False)

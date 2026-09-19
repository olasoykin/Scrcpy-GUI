from pages.base import BasePage

class DisplayPage(BasePage):
    def __init__(self, on_changed=None):
        super().__init__(title="Display", icon_name="video-display-symbolic", on_changed=on_changed)
        self._build_ui()

    def _build_ui(self):
        # Group: Video
        grp_video = self._add_group("Video")
        self.max_size = self._add_entry(grp_video, "Max Size (pixels)")
        self.max_fps = self._add_entry(grp_video, "Max FPS")
        self.video_bit_rate = self._add_entry(grp_video, "Video Bit Rate")
        
        self.video_codec = self._add_combo(
            grp_video, "Video Codec", 
            [("Default (h264)", None), ("h265", "h265"), ("av1", "av1"), ("vp8", "vp8"), ("vp9", "vp9")]
        )
        self.video_source = self._add_combo(
            grp_video, "Video Source",
            [("Default (display)", None), ("camera", "camera")]
        )

        # Group: Orientation
        grp_orientation = self._add_group("Orientation")
        self.display_orientation = self._add_combo(
            grp_orientation, "Display Orientation",
            [("Default (0°)", None), ("90°", "90"), ("180°", "180"), ("270°", "270"), 
             ("Flip 0°", "flip0"), ("Flip 90°", "flip90"), ("Flip 180°", "flip180"), ("Flip 270°", "flip270")]
        )
        self.capture_orientation = self._add_combo(
            grp_orientation, "Capture Orientation",
            [("Default (0°)", None), ("90°", "90"), ("180°", "180"), ("270°", "270"), 
             ("Flip 0°", "flip0"), ("Flip 90°", "flip90"), ("Flip 180°", "flip180"), ("Flip 270°", "flip270"), 
             ("@ (lock initial)", "@"), ("@90°", "@90"), ("@180°", "@180"), ("@270°", "@270")]
        )
        self.rotation_angle = self._add_entry(grp_orientation, "Rotation Angle (degrees)")
        self.crop = self._add_entry(grp_orientation, "Crop (width:height:x:y)")

        # Group: Rendering
        grp_rendering = self._add_group("Rendering")
        self.render_fit = self._add_combo(
            grp_rendering, "Render Fit",
            [("Default (letterbox)", None), ("Stretched", "stretched"), ("Unscaled", "unscaled")]
        )
        self.background_color = self._add_entry(grp_rendering, "Background Color (#RGB)")

        # Group: Window
        grp_window = self._add_group("Window")
        self.fullscreen = self._add_switch(grp_window, "Fullscreen", subtitle="Start in fullscreen mode")
        self.always_on_top = self._add_switch(grp_window, "Always on Top", subtitle="Keep window above others")
        self.borderless_window = self._add_switch(grp_window, "Borderless Window", subtitle="Remove window decorations")
        self.unlock_aspect_ratio = self._add_switch(grp_window, "Unlock Aspect Ratio", subtitle="Allow free window resizing")
        self.window_title = self._add_entry(grp_window, "Window Title")
        self.window_x = self._add_entry(grp_window, "Window X Position")
        self.window_y = self._add_entry(grp_window, "Window Y Position")
        self.window_width = self._add_entry(grp_window, "Window Width")
        self.window_height = self._add_entry(grp_window, "Window Height")

        # Group: Virtual Display
        grp_vd = self._add_group("Virtual Display")
        self.display_id = self._add_entry(grp_vd, "Display ID")
        self.new_display = self._add_switch(grp_vd, "New Display", subtitle="Create a new virtual display")
        self.new_display_res = self._add_resolution(
            grp_vd,
            "Resolution",
            subtitle="Virtual display width × height",
            width_placeholder="Width",
            height_placeholder="Height"
        )
        self.new_display_dpi = self._add_entry(grp_vd, "DPI")
        self.flex_display = self._add_switch(grp_vd, "Flex Display", subtitle="Resize virtual display to match window")
        self.no_vd_destroy_content = self._add_switch(grp_vd, "Keep Apps on Close", subtitle="Move apps to main display instead of destroying")
        self.no_vd_system_decorations = self._add_switch(grp_vd, "No System Decorations", subtitle="Disable virtual display system decorations")

    def get_args(self) -> list[str]:
        args = []
        val = self._entry_val(self.max_size)
        if val: args.append(f'--max-size={val}')
        val = self._entry_val(self.max_fps)
        if val: args.append(f'--max-fps={val}')
        val = self._entry_val(self.video_bit_rate)
        if val: args.append(f'--video-bit-rate={val}')
        
        val = self._combo_val(self.video_codec)
        if val: args.append(f'--video-codec={val}')
        val = self._combo_val(self.video_source)
        if val: args.append(f'--video-source={val}')

        val = self._combo_val(self.display_orientation)
        if val: args.append(f'--display-orientation={val}')
        val = self._combo_val(self.capture_orientation)
        if val: args.append(f'--capture-orientation={val}')
        val = self._entry_val(self.rotation_angle)
        if val: args.append(f'--angle={val}')
        val = self._entry_val(self.crop)
        if val: args.append(f'--crop={val}')

        val = self._combo_val(self.render_fit)
        if val: args.append(f'--render-fit={val}')
        val = self._entry_val(self.background_color)
        if val: args.append(f'--background-color={val}')

        if self.fullscreen.get_active(): args.append('--fullscreen')
        if self.always_on_top.get_active(): args.append('--always-on-top')
        if self.borderless_window.get_active(): args.append('--window-borderless')
        if self.unlock_aspect_ratio.get_active(): args.append('--no-window-aspect-ratio-lock')
        
        val = self._entry_val(self.window_title)
        if val: args.append(f'--window-title={val}')
        val = self._entry_val(self.window_x)
        if val: args.append(f'--window-x={val}')
        val = self._entry_val(self.window_y)
        if val: args.append(f'--window-y={val}')
        val = self._entry_val(self.window_width)
        if val: args.append(f'--window-width={val}')
        val = self._entry_val(self.window_height)
        if val: args.append(f'--window-height={val}')

        val = self._entry_val(self.display_id)
        if val: args.append(f'--display-id={val}')

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
        if self.no_vd_destroy_content.get_active(): args.append('--no-vd-destroy-content')
        if self.no_vd_system_decorations.get_active(): args.append('--no-vd-system-decorations')

        return args

    def reset(self) -> None:
        self.max_size.set_text('')
        self.max_fps.set_text('')
        self.video_bit_rate.set_text('')
        self.video_codec.set_selected(0)
        self.video_source.set_selected(0)
        self.display_orientation.set_selected(0)
        self.capture_orientation.set_selected(0)
        self.rotation_angle.set_text('')
        self.crop.set_text('')
        self.render_fit.set_selected(0)
        self.background_color.set_text('')
        self.fullscreen.set_active(False)
        self.always_on_top.set_active(False)
        self.borderless_window.set_active(False)
        self.unlock_aspect_ratio.set_active(False)
        self.window_title.set_text('')
        self.window_x.set_text('')
        self.window_y.set_text('')
        self.window_width.set_text('')
        self.window_height.set_text('')
        self.display_id.set_text('')
        self.new_display.set_active(False)
        self.new_display_res.set_text('')
        self.new_display_dpi.set_text('')
        self.flex_display.set_active(False)
        self.no_vd_destroy_content.set_active(False)
        self.no_vd_system_decorations.set_active(False)


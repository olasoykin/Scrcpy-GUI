from pages.base import BasePage

class CameraPage(BasePage):
    def __init__(self, on_changed=None):
        super().__init__(title="Camera", icon_name="camera-photo-symbolic", on_changed=on_changed)
        self._build_ui()

    def _build_ui(self):
        # Group "Camera Selection"
        grp_sel = self._add_group("Camera Selection")
        self.camera_facing = self._add_combo(grp_sel, "Camera Facing", [
            ("—", None),
            ("Front", "front"),
            ("Back", "back"),
            ("External", "external")
        ])
        self.camera_id = self._add_entry(grp_sel, "Camera ID")
        
        # Group "Camera Settings"
        grp_set = self._add_group("Camera Settings")
        self.camera_size = self._add_resolution(
            grp_set,
            "Camera Size",
            subtitle="Camera resolution width × height",
            width_placeholder="Width",
            height_placeholder="Height"
        )
        self.camera_fps = self._add_entry(grp_set, "Camera FPS")
        self.camera_ar = self._add_entry(grp_set, "Camera Aspect Ratio")
        self.camera_zoom = self._add_entry(grp_set, "Camera Zoom")
        self.high_speed = self._add_switch(grp_set, "High Speed Mode", "Enable high-speed camera capture")
        self.camera_torch = self._add_switch(grp_set, "Camera Torch", "Turn on flash/torch when camera starts")

    def get_args(self) -> list[str]:
        camera_args = []
        val = self._combo_val(self.camera_facing)
        if val: camera_args.append(f'--camera-facing={val}')
        
        val = self._entry_val(self.camera_id)
        if val: camera_args.append(f'--camera-id={val}')
        
        val = self._entry_val(self.camera_size)
        if val: camera_args.append(f'--camera-size={val}')
        
        val = self._entry_val(self.camera_fps)
        if val: camera_args.append(f'--camera-fps={val}')
        
        val = self._entry_val(self.camera_ar)
        if val: camera_args.append(f'--camera-ar={val}')
        
        val = self._entry_val(self.camera_zoom)
        if val: camera_args.append(f'--camera-zoom={val}')
        
        if self.high_speed.get_active(): camera_args.append('--camera-high-speed')
        if self.camera_torch.get_active(): camera_args.append('--camera-torch')
        
        if camera_args:
            return ['--video-source=camera'] + camera_args
        return []

    def reset(self):
        self.camera_facing.set_selected(0)
        self.camera_id.set_text('')
        self.camera_size.set_text('')
        self.camera_fps.set_text('')
        self.camera_ar.set_text('')
        self.camera_zoom.set_text('')
        self.high_speed.set_active(False)
        self.camera_torch.set_active(False)

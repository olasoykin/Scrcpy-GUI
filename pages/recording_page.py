from pages.base import BasePage

class RecordingPage(BasePage):
    def __init__(self, on_changed=None):
        super().__init__(title="Recording", icon_name="media-record-symbolic", on_changed=on_changed)
        self._build_ui()

    def _build_ui(self):
        # Group "Recording"
        grp_rec = self._add_group("Recording")
        self.record_file = self._add_entry(grp_rec, "Record File (path)")
        self.record_format = self._add_combo(grp_rec, "Record Format", [
            ("Auto (from extension)", None),
            ("MP4", "mp4"),
            ("MKV", "mkv"),
            ("M4A", "m4a"),
            ("MKA", "mka"),
            ("Opus", "opus"),
            ("AAC", "aac"),
            ("FLAC", "flac"),
            ("WAV", "wav")
        ])
        self.record_orientation = self._add_combo(grp_rec, "Record Orientation", [
            ("Default (0°)", None),
            ("90°", "90"),
            ("180°", "180"),
            ("270°", "270")
        ])
        self.time_limit = self._add_entry(grp_rec, "Time Limit (seconds)")

        # Group "Playback"
        grp_play = self._add_group("Playback")
        self.no_playback = self._add_switch(grp_play, "No Playback", "Disable all playback on computer")
        self.no_video_playback = self._add_switch(grp_play, "No Video Playback", "Disable video playback on computer")
        self.no_audio_playback = self._add_switch(grp_play, "No Audio Playback", "Disable audio playback on computer")

    def get_args(self) -> list[str]:
        args = []
        val = self._entry_val(self.record_file)
        if val: args.append(f'--record={val}')
        
        val = self._combo_val(self.record_format)
        if val: args.append(f'--record-format={val}')
        
        val = self._combo_val(self.record_orientation)
        if val: args.append(f'--record-orientation={val}')
        
        val = self._entry_val(self.time_limit)
        if val: args.append(f'--time-limit={val}')
        
        if self.no_playback.get_active(): args.append('--no-playback')
        if self.no_video_playback.get_active(): args.append('--no-video-playback')
        if self.no_audio_playback.get_active(): args.append('--no-audio-playback')
        
        return args

    def reset(self):
        self.record_file.set_text('')
        self.record_format.set_selected(0)
        self.record_orientation.set_selected(0)
        self.time_limit.set_text('')
        self.no_playback.set_active(False)
        self.no_video_playback.set_active(False)
        self.no_audio_playback.set_active(False)

from pages.base import BasePage

class AudioPage(BasePage):
    def __init__(self, on_changed=None):
        super().__init__(title="Audio", icon_name="audio-volume-high-symbolic", on_changed=on_changed)
        self._build_ui()

    def _build_ui(self):
        grp_audio = self._add_group("Audio")
        
        self.no_audio = self._add_switch(grp_audio, "No Audio", subtitle="Disable audio forwarding")
        
        self.audio_source = self._add_combo(
            grp_audio, "Audio Source",
            [("Default (output)", None), ("Playback", "playback"), ("Microphone", "mic"), 
             ("Mic Unprocessed", "mic-unprocessed"), ("Mic Camcorder", "mic-camcorder"), 
             ("Mic Voice Recognition", "mic-voice-recognition"), ("Mic Voice Communication", "mic-voice-communication"), 
             ("Voice Call", "voice-call"), ("Voice Call Uplink", "voice-call-uplink"), 
             ("Voice Call Downlink", "voice-call-downlink"), ("Voice Performance", "voice-performance")]
        )
        
        self.audio_codec = self._add_combo(
            grp_audio, "Audio Codec",
            [("Default (opus)", None), ("AAC", "aac"), ("FLAC", "flac"), ("Raw", "raw")]
        )
        
        self.audio_bit_rate = self._add_entry(grp_audio, "Audio Bit Rate")
        self.audio_buffer = self._add_entry(grp_audio, "Audio Buffer (ms)")
        self.duplicate_audio = self._add_switch(grp_audio, "Duplicate Audio", subtitle="Keep playing audio on device too")

    def get_args(self) -> list[str]:
        args = []
        if self.no_audio.get_active(): args.append('--no-audio')
        
        val = self._combo_val(self.audio_source)
        if val: args.append(f'--audio-source={val}')
        
        val = self._combo_val(self.audio_codec)
        if val: args.append(f'--audio-codec={val}')
        
        val = self._entry_val(self.audio_bit_rate)
        if val: args.append(f'--audio-bit-rate={val}')
        
        val = self._entry_val(self.audio_buffer)
        if val: args.append(f'--audio-buffer={val}')
        
        if self.duplicate_audio.get_active(): args.append('--audio-dup')
        
        return args

    def reset(self) -> None:
        self.no_audio.set_active(False)
        self.audio_source.set_selected(0)
        self.audio_codec.set_selected(0)
        self.audio_bit_rate.set_text('')
        self.audio_buffer.set_text('')
        self.duplicate_audio.set_active(False)

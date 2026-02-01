import torch
import numpy as np
from silero_vad import get_speech_timestamps, load_silero_vad
from modules.stt.logger import log

class SileroVAD:
    def __init__(self, sample_rate=16000):
        self.sample_rate = sample_rate
        self.model = load_silero_vad()

    def has_speech(self, audio: np.ndarray) -> bool:
        audio_tensor = torch.from_numpy(audio).float()

        timestamps = get_speech_timestamps(
            audio_tensor,
            self.model,
            sampling_rate=self.sample_rate,
            min_speech_duration_ms=300,
            min_silence_duration_ms=400
        )
        log(f"VAD detected speech: {len(timestamps) > 0}", role="PIPELINE", stage="VAD", payload=f"{len(audio)} samples")
        return len(timestamps) > 0

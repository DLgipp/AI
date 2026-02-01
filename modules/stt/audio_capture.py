import sounddevice as sd
import numpy as np
from config import SAMPLE_RATE, CHANNELS, FRAME_DURATION


def record_frame() -> np.ndarray:
    frames = int(SAMPLE_RATE * FRAME_DURATION)
    audio = sd.rec(
        frames,
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="float32"
    )
    sd.wait()
    return audio.flatten()

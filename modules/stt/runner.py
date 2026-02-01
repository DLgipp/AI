import time
import numpy as np
from collections import deque

from modules.stt.audio_capture import record_frame
from modules.stt.whisper_stt import WhisperSTT
from modules.stt.vad import SileroVAD
from config import MAX_SPEECH_DURATION

from datetime import datetime


FRAME_DURATION = 0.5
VAD_WINDOW_SECONDS = 1.5
VAD_FRAMES = int(VAD_WINDOW_SECONDS / FRAME_DURATION)

SILENCE_FRAMES_TO_END = 3
PRE_SPEECH_FRAMES = 2
POST_SPEECH_FRAMES = 2

from modules.stt.logger import log

def run_stt_loop():
    stt = WhisperSTT()
    vad = SileroVAD()

    frame_buffer = deque(maxlen=VAD_FRAMES)
    pre_speech_buffer = deque(maxlen=PRE_SPEECH_FRAMES)
    speech_buffer = []

    speech_active = False
    silence_counter = 0
    post_speech_counter = 0
    speech_start_time = None

    log("Real-time режим с padding запущен. Говорите...", role="SYSTEM", stage="stt_loop")

    while True:
        frame = record_frame()
        if len(pre_speech_buffer) != 0:
            frame_buffer.append(frame)
        pre_speech_buffer.append(frame)

        if len(frame_buffer) < VAD_FRAMES:
            continue

        vad_audio = np.concatenate(frame_buffer)
        has_speech = vad.has_speech(vad_audio)

        if has_speech:
            silence_counter = 0
            post_speech_counter = 0

            if not speech_active:
                speech_active = True
                speech_start_time = time.time()
                speech_buffer = list(pre_speech_buffer)
                log("Speech detected, starting capture", role="PIPELINE", stage="vad")
            speech_buffer.append(frame)

        else:
            if speech_active:
                silence_counter += 1
                speech_buffer.append(frame)

                if silence_counter >= SILENCE_FRAMES_TO_END:
                    post_speech_counter += 1

                    if post_speech_counter >= POST_SPEECH_FRAMES:
                        speech_active = False
                        silence_counter = 0
                        post_speech_counter = 0

                        audio = np.concatenate(speech_buffer)
                        speech_buffer = []
                        log("Speech segment captured, sending to STT", role="PIPELINE", stage="stt_loop", payload=f"{len(audio)} samples")

                        try:
                            text = stt.transcribe(audio)
                            if text:
                                log(f"Transcription result: {text}", role="USER", stage="stt", payload=None)
                                return text
                        except Exception as e:
                            log(f"STT error: {e}", role="ERROR", stage="stt")

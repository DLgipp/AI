import time
import numpy as np
from collections import deque
import asyncio

from modules.stt.audio_capture import record_frame
from modules.stt.whisper_stt import WhisperSTT
from modules.stt.vad import SileroVAD
from modules.stt.logger import log

from modules.events.event import Event

from config import FRAME_DURATION, VAD_WINDOW_SECONDS

VAD_FRAMES = int(VAD_WINDOW_SECONDS / FRAME_DURATION)
SILENCE_FRAMES_TO_END = 2
POST_SPEECH_FRAMES = 2
PRE_SPEECH_FRAMES = 1

class STTController:
    def __init__(self, bus, silence_timeout=10):
        self.bus = bus
        self.silence_timeout = silence_timeout

        self.stt = WhisperSTT()
        self.vad = SileroVAD()

        self.frame_buffer = deque(maxlen=VAD_FRAMES)
        self.pre_speech_buffer = deque(maxlen=PRE_SPEECH_FRAMES)
        self.speech_buffer = []

        self.speech_active = False
        self.silence_counter = 0
        self.post_speech_counter = 0

        self.last_activity_ts = time.time()

        log("STTController initialized", role="SYSTEM", stage="STT")

    def tick(self):
        frame = record_frame()
        now = time.time()

        self.pre_speech_buffer.append(frame)
        self.frame_buffer.append(frame)

        # 1. Ждём, пока наберётся окно VAD
        if len(self.frame_buffer) < VAD_FRAMES:
            return

        vad_audio = np.concatenate(self.frame_buffer)
        has_speech = self.vad.has_speech(vad_audio)

        # 2. Есть речь
        if has_speech:
            self.last_activity_ts = now
            self.silence_counter = 0
            self.post_speech_counter = 0

            if not self.speech_active:
                self.speech_active = True
                self.speech_buffer = list(self.pre_speech_buffer)
                self.bus.emit(Event("speech_start"))
                log("Speech started", role="PIPELINE", stage="VAD")

            self.speech_buffer.append(frame)
            return

        # 3. Речь закончилась
        if self.speech_active:
            self.silence_counter += 1
            self.speech_buffer.append(frame)

            if self.silence_counter >= SILENCE_FRAMES_TO_END:
                self.post_speech_counter += 1

                if self.post_speech_counter >= POST_SPEECH_FRAMES:
                    self._finalize_speech()
            return

        # 4. Полная тишина
        if now - self.last_activity_ts >= self.silence_timeout:
            self.bus.emit(Event("silence_timeout", {
                "duration": int(now - self.last_activity_ts)
            }))
            self.last_activity_ts = now


    def _finalize_speech(self):
        audio = np.concatenate(self.speech_buffer)

        self.speech_active = False
        self.speech_buffer = []
        self.silence_counter = 0
        self.post_speech_counter = 0

        self.last_activity_ts = time.time()

        log("Speech finalized", role="PIPELINE", stage="STT")

        try:
            text = self.stt.transcribe(audio)
            if text:
                log(f"Transcribed text: {text}", role="USER", stage="STT")
                self.bus.emit(Event("user_text", {"text": text}))
        except Exception as e:
            self.bus.emit(Event("stt_error", {"error": str(e)}))


async def stt_loop(stt: STTController):
    """Асинхронный цикл STT."""
    loop = asyncio.get_event_loop()
    while True:
        # tick() выполняется в отдельном потоке
        await loop.run_in_executor(None, stt.tick)
        await asyncio.sleep(0.02)

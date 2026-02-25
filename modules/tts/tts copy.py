import time
import asyncio
import torch
import sounddevice as sd
import numpy as np

from qwen_tts import Qwen3TTSModel
from modules.stt.logger import log
from modules.events.timers import SilenceTimer
import re

import threading
import queue



audio_queue = queue.Queue(maxsize=4)
stop_event = threading.Event()

ref_audio = "./modules/tts/origin1.wav"
ref_text = "Да пофиг, что он - красавчик! Я таких не перевариваю. Видно же что я фанатка, рас повесила брелок на сумку! По вашему нормально вот так смеятся над чужими увлечениями?"

model = Qwen3TTSModel.from_pretrained(
    "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
    device_map="cuda:0",
    dtype=torch.bfloat16,
)

# Глобальный поток вывода
audio_stream = None

def audio_worker(sample_rate: int):
    stream = sd.OutputStream(
        samplerate=sample_rate,
        channels=1,
        dtype='float32'
    )
    stream.start()

    while not stop_event.is_set():
        try:
            chunk = audio_queue.get(timeout=0.1)
            stream.write(chunk)
        except queue.Empty:
            continue

    stream.stop()
    stream.close()

def generate_worker(text: str):
    sentences = re.split(r'(?<=[.!?])\s+', text)

    for sentence in sentences:
        wavs, sr = model.generate_voice_clone(
            text=sentence,
            language="Russian",
            ref_audio=ref_audio,
            ref_text=ref_text,
        )

        audio = np.array(wavs[0], dtype=np.float32)

        audio_queue.put(audio)


def _speak_blocking(text: str, silence_timer: SilenceTimer):
    silence_timer.activity_start()

    try:
        log("Parallel TTS started", role="PIPELINE", stage="TTS")

        stop_event.clear()

        # Запускаем генерацию
        gen_thread = threading.Thread(target=generate_worker, args=(text,))
        gen_thread.start()

        # Ждём первый кусок, чтобы узнать sample rate
        wavs, sr = model.generate_voice_clone(
            text=".",
            language="Russian",
            ref_audio=ref_audio,
            ref_text=ref_text,
        )

        # Запускаем плеер
        player_thread = threading.Thread(target=audio_worker, args=(sr,))
        player_thread.start()

        gen_thread.join()

        # Ждём пока очередь опустеет
        while not audio_queue.empty():
            time.sleep(0.05)

        stop_event.set()
        player_thread.join()

        log("Parallel TTS finished", role="PIPELINE", stage="TTS")

    except Exception as e:
        log(f"TTS error: {e}", role="ERROR", stage="TTS")

    finally:
        silence_timer.activity_end()


async def speak_async(text: str, silence_timer: SilenceTimer, loop=None):
    if loop is None:
        loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _speak_blocking, text, silence_timer)
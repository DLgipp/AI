#import pyttsx3
import time
import asyncio
from modules.stt.logger import log
from modules.events.timers import SilenceTimer

import torch
import sounddevice as sd
import numpy as np
import soundfile as sf
from qwen_tts import Qwen3TTSModel
#import re

VOICE_ID = r'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_RU-RU_IRINA_11.0'
RATE = 200
VOLUME = 1.0

ref_audio = "./modules/tts/origin1.wav"
ref_text  = "Да пофиг, что он - красавчик! Я таких не перевариваю. Видно же что я фанатка, рас повесила брелок на сумку! По вашему нормально вот так смеятся над чужими увлечениями? "
model = Qwen3TTSModel.from_pretrained(
    "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
    device_map="cuda:0",
    dtype=torch.bfloat16,
    #attn_implementation="flash_attention_2",
)


def _speak_blocking(text: str, silence_timer: SilenceTimer):
    silence_timer.activity_start()
    """Оригинальная синхронная функция speak."""
    try:
        start_time = time.time()
        log("TTS synthesis started", role="PIPELINE", stage="TTS", payload=f"{len(text)} chars")
        
        """engine = pyttsx3.init()
        engine.setProperty('voice', VOICE_ID)
        engine.setProperty('rate', RATE)
        engine.setProperty('volume', VOLUME)

        engine.say(text)
        engine.runAndWait()
        engine.stop()

        """
        wavs, sr = model.generate_voice_clone(
        text=text,
        language="Russian",
        ref_audio=ref_audio,
        ref_text=ref_text,
    )
        sd.play(np.array(wavs[0]), samplerate=sr)
        sd.wait() 
        end_time = time.time()
        log(f"TTS synthesis finished. Duration: {end_time - start_time:.2f} sec",
            role="PIPELINE", stage="TTS", payload=f"{len(text)} chars")

        log(f"Text spoken: {text}", role="ASSISTANT", stage="TTS")

    except Exception as e:
        log(f"TTS error: {e}", role="ERROR", stage="TTS")
    finally:
        silence_timer.activity_end()

async def speak_async(text: str, silence_timer: SilenceTimer, loop=None):
    """Асинхронная обёртка для TTS."""
    _speak_blocking(text, silence_timer)
    #loop = asyncio.get_event_loop()
    #await loop.run_in_executor(None, _speak_blocking, text, silence_timer)

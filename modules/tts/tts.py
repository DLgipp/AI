import pyttsx3
import time
import asyncio
from modules.stt.logger import log
from modules.events.timers import SilenceTimer

VOICE_ID = r'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_RU-RU_IRINA_11.0'
RATE = 200
VOLUME = 1.0

def _speak_blocking(text: str, silence_timer: SilenceTimer):
    silence_timer.activity_start()
    """Оригинальная синхронная функция speak."""
    try:
        start_time = time.time()
        log("TTS synthesis started", role="PIPELINE", stage="TTS", payload=f"{len(text)} chars")

        engine = pyttsx3.init()
        engine.setProperty('voice', VOICE_ID)
        engine.setProperty('rate', RATE)
        engine.setProperty('volume', VOLUME)

        engine.say(text)
        engine.runAndWait()
        engine.stop()

        end_time = time.time()
        log(f"TTS synthesis finished. Duration: {end_time - start_time:.2f} sec",
            role="PIPELINE", stage="TTS", payload=f"{len(text)} chars")

        log(f"Text spoken: {text}", role="ASSISTANT", stage="TTS")

    except Exception as e:
        log(f"TTS error: {e}", role="ERROR", stage="TTS")
    finally:
        silence_timer.activity_end()

async def speak_async(text: str, silence_timer: SilenceTimer):
    """Асинхронная обёртка для TTS."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _speak_blocking, text, silence_timer)

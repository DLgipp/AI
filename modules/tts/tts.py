import pyttsx3
import time
from modules.stt.logger import log  # используем уже готовый модуль логов

VOICE_ID = r'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_RU-RU_IRINA_11.0'
RATE = 200
VOLUME = 1.0

def speak(text: str):
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
        log(
            f"TTS synthesis finished. Duration: {end_time - start_time:.2f} sec",
            role="PIPELINE",
            stage="TTS",
            payload=f"{len(text)} chars"
        )

        log(f"Text spoken: {text}", role="ASSISTANT", stage="TTS")

    except Exception as e:
        log(f"TTS error: {e}", role="ERROR", stage="TTS")

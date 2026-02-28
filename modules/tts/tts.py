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

from .tts_expression import convert_to_ssml, ExpressionContext, validate_ssml, strip_ssml


audio_queue = queue.Queue(maxsize=4)
language = 'ru'
model_id = 'v5_ru'
device = torch.device('cuda')
model, example_text = torch.hub.load(repo_or_dir='snakers4/silero-models',
                                     model='silero_tts',
                                     language=language,
                                     speaker=model_id)
model.to(device)  # gpu or cpu
sample_rate = 48000
speaker = 'kseniya'
put_accent=True
put_yo=True
put_stress_homo=True
put_yo_homo=True
stop_event = threading.Event()

# Глобальное хранилище контекста для выразительности
_tts_context = {}

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

def generate_worker(text: str, use_ssml: bool = True, context: ExpressionContext = None):
    """
    Generate audio from text with optional SSML enhancement.

    Args:
        text: Input text or SSML
        use_ssml: Whether to convert text to SSML for expression
        context: Emotional context for SSML generation
    """
    ssml_text = None
    use_fallback = False

    # Convert to SSML if context provided and SSML enabled
    if use_ssml and context:
        try:
            ssml_text = convert_to_ssml(
                text=text,
                emotion=context.emotion,
                emotional_tone=context.emotional_tone,
                decision_strategy=context.decision_strategy,
                dominant_trait=context.dominant_trait,
                engagement_level=context.engagement_level,
                user_emotion=context.user_emotion,
                validate=True,
                repair=True
            )

            # Check if we got SSML or plain text fallback
            if ssml_text == text:
                log("TTS: SSML conversion returned plain text fallback",
                    role="DEBUG", stage="TTS")
                use_fallback = True
            else:
                log(f"TTS: Using SSML for expressive speech, len={len(ssml_text)}",
                    role="DEBUG", stage="TTS")

                # Validate SSML before passing to TTS
                is_valid, error = validate_ssml(ssml_text)
                if not is_valid:
                    log(f"TTS: SSML validation failed, using plain text: {error}",
                        role="WARN", stage="TTS")
                    use_fallback = True
                    ssml_text = None

        except Exception as e:
            log(f"TTS: SSML conversion error, using plain text: {e}",
                role="ERROR", stage="TTS")
            use_fallback = True
            ssml_text = None

    # Use SSML if available and valid
    if ssml_text and not use_fallback:
        try:
            audio = model.apply_tts(ssml_text=ssml_text,
                                    speaker=speaker,
                                    sample_rate=sample_rate)
            audio = np.array(audio, dtype=np.float32)
            audio_queue.put(audio)
        except Exception as e:
            # SSML failed, fallback to plain text
            log(f"TTS: SSML synthesis failed, falling back to plain text: {e}",
                role="WARN", stage="TTS")
            sentences = re.split(r'(?<=[.!?])\s+', text)
            for sentence in sentences:
                if not sentence or len(sentence) < 2:
                    continue
                audio = model.apply_tts(text=sentence,
                                        speaker=speaker,
                                        sample_rate=sample_rate)
                audio = np.array(audio, dtype=np.float32)
                audio_queue.put(audio)
    else:
        # Fallback to plain text processing
        sentences = re.split(r'(?<=[.!?])\s+', text)

        for sentence in sentences:
            if not sentence or len(sentence) < 2:
                continue
            audio = model.apply_tts(text=sentence,
                                    speaker=speaker,
                                    sample_rate=sample_rate)

            audio = np.array(audio, dtype=np.float32)
            audio_queue.put(audio)


def _speak_blocking(text: str, silence_timer: SilenceTimer, context: ExpressionContext = None):
    silence_timer.activity_start()

    try:
        log("Parallel TTS started", role="PIPELINE", stage="TTS")

        stop_event.clear()

        # Запускаем генерацию с контекстом
        gen_thread = threading.Thread(target=generate_worker, args=(text, True, context))
        gen_thread.start()

        # Запускаем плеер
        player_thread = threading.Thread(target=audio_worker, args=(sample_rate,))
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


async def speak_async(text: str, silence_timer: SilenceTimer, context: ExpressionContext = None, loop=None):
    if loop is None:
        loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _speak_blocking, text, silence_timer, context)


def set_context(context: ExpressionContext):
    """Set global TTS context for subsequent calls."""
    global _tts_context
    _tts_context = context.to_dict() if context else {}


def get_context() -> ExpressionContext:
    """Get current TTS context."""
    if _tts_context:
        return ExpressionContext(**_tts_context)
    return ExpressionContext()


def clear_context():
    """Clear global TTS context."""
    global _tts_context
    _tts_context = {}
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

# Discord callback для отправки аудио
_discord_audio_callback = None
_discord_audio_queue = queue.Queue(maxsize=100)

# Константы для Discord
DISCORD_SAMPLE_RATE = 48000
DISCORD_CHUNK_SIZE = 960  # 20ms при 48kHz


def set_discord_audio_callback(callback):
    """
    Установить callback для отправки аудио данных в Discord.

    Args:
        callback: Функция, принимающая numpy array с аудио данными
    """
    global _discord_audio_callback
    _discord_audio_callback = callback


def get_discord_audio_callback():
    """Получить текущий callback для Discord."""
    return _discord_audio_callback


def _send_to_discord(audio_data: np.ndarray):
    """
    Отправить аудио в Discord, разбив на чанки по 20ms.
    
    Args:
        audio_data: Numpy array с аудио (float32, -1 до 1)
    """
    if _discord_audio_callback is None:
        return
    
    import time
    
    # Проверка формата аудио
    if audio_data.dtype != np.float32:
        log(f"Warning: Audio dtype is {audio_data.dtype}, expected float32",
            role="WARN", stage="TTS")
        audio_data = audio_data.astype(np.float32)
    
    # Проверка диапазона значений
    audio_min = np.min(audio_data)
    audio_max = np.max(audio_data)
    if audio_min < -1.0 or audio_max > 1.0:
        log(f"Warning: Audio range [{audio_min:.2f}, {audio_max:.2f}], expected [-1, 1]",
            role="WARN", stage="TTS")
        # Нормализация если нужно
        max_val = max(abs(audio_min), abs(audio_max))
        if max_val > 0:
            audio_data = audio_data / max_val
    
    # Разбиваем на чанки по DISCORD_CHUNK_SIZE сэмплов (960 = 20ms при 48kHz)
    chunk_count = 0
    for i in range(0, len(audio_data), DISCORD_CHUNK_SIZE):
        chunk = audio_data[i:i + DISCORD_CHUNK_SIZE]
        
        # Если чанк меньше нужного, дополняем тишиной
        if len(chunk) < DISCORD_CHUNK_SIZE:
            import numpy as np
            chunk = np.pad(chunk, (0, DISCORD_CHUNK_SIZE - len(chunk)), 
                          mode='constant', constant_values=0)
        
        # Проверка размера чанка
        if len(chunk) != DISCORD_CHUNK_SIZE:
            log(f"Warning: Chunk size {len(chunk)}, expected {DISCORD_CHUNK_SIZE}",
                role="WARN", stage="TTS")
        
        _discord_audio_callback(chunk)
        chunk_count += 1
        
        # Небольшая задержка чтобы Discord успевал обрабатывать
        # Но не слишком большая чтобы не замедлять
        if chunk_count % 10 == 0:  # Каждые 10 чанков (200ms)
            time.sleep(0.01)  # 10ms задержка
    
    audio_duration_ms = int(len(audio_data) / DISCORD_SAMPLE_RATE * 1000)
    log(f"Sent {chunk_count} chunks to Discord ({audio_duration_ms}ms of audio, {len(audio_data)} samples)",
        role="DEBUG", stage="TTS")

def audio_worker(sample_rate: int):
    """
    Worker для воспроизведения аудио.

    Отправляет аудио данные:
    1. В локальный динамик (sounddevice)
    2. В Discord уже отправлено из generate_worker
    """
    stream = sd.OutputStream(
        samplerate=sample_rate,
        channels=1,
        dtype='float32',
        device=68
    )
    stream.start()

    log(f"Audio worker started, sample_rate={sample_rate}",
        role="DEBUG", stage="TTS")

    while not stop_event.is_set():
        try:
            chunk = audio_queue.get(timeout=0.1)

            # Воспроизведение локально
            stream.write(chunk)

            # Discord уже получил аудио из generate_worker
            # Здесь только локальное воспроизведение

        except queue.Empty:
            continue

    stream.stop()
    stream.close()
    log("Audio worker stopped", role="DEBUG", stage="TTS")

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
            
            # Отправляем в локальную очередь
            audio_queue.put(audio)
            
            # Отправляем в Discord (разбив на чанки)
            _send_to_discord(audio)
            
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
                _send_to_discord(audio)
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
            _send_to_discord(audio)


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
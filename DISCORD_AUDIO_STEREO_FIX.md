# Discord Audio - Исправление искажения звука

## 🐛 Проблема

Скорость воспроизведения была правильной, но звук искажен.

**Причина:** Discord ожидает **стерео** аудио (3840 байт на фрейм), а отправлялось **моно** (1920 байт).

---

## ✅ Решение

### 1. Конвертация Mono → Stereo

**Исправление в `modules/discord/voice_client.py`:**

```python
def add_audio_chunk(self, audio_data: np.ndarray):
    # Конвертируем в 16-bit PCM
    pcm_chunk = (audio_data * 32767).astype(np.int16)
    
    # Конвертируем mono в stereo путём чередования
    stereo_chunk = np.empty(len(pcm_chunk) * 2, dtype=np.int16)
    stereo_chunk[0::2] = pcm_chunk  # Левый канал
    stereo_chunk[1::2] = pcm_chunk  # Правый канал
    
    stereo_bytes = stereo_chunk.tobytes()  # 3840 байт
```

### 2. Проверка формата аудио

**Исправление в `modules/tts/tts.py`:**

```python
def _send_to_discord(audio_data: np.ndarray):
    # Проверка формата
    if audio_data.dtype != np.float32:
        audio_data = audio_data.astype(np.float32)
    
    # Проверка диапазона [-1, 1]
    if audio_min < -1.0 or audio_max > 1.0:
        audio_data = audio_data / max_val  # Нормализация
```

---

## 📊 Формат аудио для Discord

| Параметр | Значение |
|----------|----------|
| Sample Rate | 48 kHz |
| Bit Depth | 16-bit |
| Channels | 2 (Stereo) |
| Frame Size | 960 samples (20ms) |
| Frame Bytes | 3840 bytes (960 × 2 × 2) |

---

## 🔍 Ожидаемые логи

### Успешная отправка:

```
[TTS] Sent 250 chunks to Discord (5000ms of audio, 120000 samples)
[DISCORD_STREAM] Audio chunk added: mono_samples=960, stereo_bytes=3840, queue_size=1
[DISCORD_STREAM] Audio chunk added: mono_samples=960, stereo_bytes=3840, queue_size=2
```

**Ключевые моменты:**
- `mono_samples=960` - правильный размер входного чанка
- `stereo_bytes=3840` - правильный размер после конвертации

---

## 🧪 Тестирование

### 1. Запустите проект:

```bash
cd c:\AI
python main.py
```

### 2. Скажите что-нибудь ассистенту

### 3. Проверьте логи

Ищите:
```
[DISCORD_STREAM] Audio chunk added: mono_samples=960, stereo_bytes=3840
```

### 4. Проверьте звук в Discord

Вы должны слышать **чистый звук без искажений**.

---

## 🎵 Сравнение

### До исправления:

```
Mono:  [L][L][L][L]...  (960 samples = 1920 bytes)
                    ↓
Discord expects: [L][R][L][R][L][R][L][R]...  (1920 samples = 3840 bytes)
```

**Результат:** Искажения, неправильный формат

### После исправления:

```
Mono:  [L][L][L][L]...  (960 samples)
                    ↓
Stereo: [L][L][L][L][L][L][L][L]...  (960 left + 960 right = 1920 samples = 3840 bytes)
                    ↓
Discord: ✓ Правильный формат
```

**Результат:** Чистый звук

---

## 🐛 Возможные проблемы

### Всё ещё есть искажения

**Проверьте логи:**

```
[TTS] Warning: Audio dtype is int16, expected float32
[TTS] Warning: Audio range [-32768, 32767], expected [-1, 1]
[DISCORD_STREAM] Warning: Expected 3840 bytes, got 1920
```

**Решение:**
- Проверьте что TTS генерирует float32 в диапазоне [-1, 1]
- Проверьте что `StreamingAudioSource` конвертирует в stereo

### Звук слишком тихий

**Решение:** Увеличьте громкость:

```python
# В config.py
DISCORD_DEFAULT_VOLUME = 1.5  # 150%
```

### Звук прерывается

**Решение:** Увеличьте буфер:

```python
# В StreamingAudioSource.__init__
self._audio_queue = queue.Queue(maxsize=500)  # Больше чанков в буфере
```

---

## ✅ Чеклист

- [ ] В логах: `mono_samples=960`
- [ ] В логах: `stereo_bytes=3840`
- [ ] Нет предупреждений о формате
- [ ] Звук чистый без искажений
- [ ] Звук нормальной скорости

---

## 📝 Технические детали

### Почему stereo?

Discord использует стерео формат даже для моно источников:
- Левый канал = Правый канал (для моно)
- 960 сэмплов × 2 канала = 1920 сэмплов на фрейм
- 1920 сэмплов × 2 байта = 3840 байт

### Почему чередование (interleaving)?

Аудио данные в стерео хранятся как:
```
[L0][R0][L1][R1][L2][R2]...
```

Где:
- `L0` = левый канал, сэмпл 0
- `R0` = правый канал, сэмпл 0

Для моно: `L0 = R0`, `L1 = R1`, и т.д.

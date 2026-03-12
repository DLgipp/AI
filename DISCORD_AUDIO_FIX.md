# Discord Audio Streaming - Исправление скорости воспроизведения

## 🐛 Проблема

Аудио в Discord воспроизводилось слишком быстро и искаженно.

**Лог:**
```
[TTS] Sending audio chunk to Discord: shape=(531000,), dtype=float32
```

Один огромный чанк (531000 сэмплов = ~11 секунд) отправлялся в Discord, что приводило к:
- Слишком быстрому воспроизведению
- Искажению звука
- Неправильной скорости

---

## ✅ Решение

### 1. Разбиение аудио на правильные чанки

Discord ожидает чанки по **960 сэмплов** (20ms при 48kHz).

**Исправление в `modules/tts/tts.py`:**

```python
DISCORD_CHUNK_SIZE = 960  # 20ms при 48kHz

def _send_to_discord(audio_data: np.ndarray):
    # Разбиваем на чанки по 960 сэмплов
    for i in range(0, len(audio_data), DISCORD_CHUNK_SIZE):
        chunk = audio_data[i:i + DISCORD_CHUNK_SIZE]
        # Дополняем тишиной если нужно
        _discord_audio_callback(chunk)
```

### 2. Отправка из `generate_worker`

Теперь аудио отправляется в Discord сразу после генерации, а не из `audio_worker`:

```python
audio = model.apply_tts(...)
audio_queue.put(audio)      # Локальное воспроизведение
_send_to_discord(audio)     # Отправка в Discord
```

### 3. Правильная буферизация в Discord

**Исправление в `modules/discord/voice_client.py`:**

```python
class StreamingAudioSource:
    def add_audio_chunk(self, audio_data: np.ndarray):
        # Конвертируем в 16-bit PCM
        pcm_chunk = (audio_data * 32767).astype(np.int16)
        pcm_bytes = pcm_chunk.tobytes()
        
        # Discord ожидает 3840 байт
        if len(pcm_bytes) < 3840:
            pcm_bytes = pcm_bytes + (b'\x00' * (3840 - len(pcm_bytes)))
        
        self._audio_queue.put(pcm_bytes)
```

### 4. Синхронизация отправки

Добавлена небольшая задержка при отправке чанков:

```python
if chunk_count % 10 == 0:  # Каждые 200ms
    time.sleep(0.01)  # 10ms задержка
```

---

## 📊 Ожидаемые логи

### При запуске:

```
[SYSTEM] [DISCORD] Discord bot logged in as YourBot#1234
[SYSTEM] [DISCORD_READY] Discord: Joined voice channel 987654321
[SYSTEM] [DISCORD_READY] Discord: Audio streaming will auto-start on first TTS
```

### Когда ассистент говорит:

```
[TTS] [LOCAL] TTS: Привет! Как дела?
[TTS] [DEBUG] Audio worker started, sample_rate=48000
[TTS] [DEBUG] Sent 250 chunks to Discord (5000ms of audio)  ← 5 секунд аудио
[DISCORD_STREAM] [DEBUG] Auto-starting audio stream on first chunk
[SYSTEM] [DISCORD_STREAM] Audio stream started: volume=1.0
[DISCORD_STREAM] [DEBUG] Audio chunk added: samples=960, bytes=3840, queue_size=1
[DISCORD_STREAM] [DEBUG] Audio chunk added: samples=960, bytes=3840, queue_size=2
...
```

**Ключевые моменты:**
- `samples=960` - правильный размер чанка
- `bytes=3840` - правильный размер в байтах
- `Sent XXX chunks to Discord (XXXms of audio)` - общая длительность

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
[TTS] Sent XXX chunks to Discord (XXXms of audio)
[DISCORD_STREAM] Audio chunk added: samples=960, bytes=3840
```

### 4. Проверьте звук в Discord

Вы должны слышать нормальную, не искаженную речь с правильной скоростью.

---

## 🔧 Настройка производительности

Если всё ещё есть проблемы со скоростью, попробуйте настроить задержку:

```python
# В modules/tts/tts.py, функция _send_to_discord

# Более частая синхронизация (каждые 100ms)
if chunk_count % 5 == 0:
    time.sleep(0.005)  # 5ms задержка

# Или менее частая (каждые 500ms)
if chunk_count % 25 == 0:
    time.sleep(0.02)  # 20ms задержка
```

---

## 📝 Примечания

### Почему 960 сэмплов?

- Discord использует 20ms фреймы
- При 48kHz: 48000 × 0.020 = 960 сэмплов
- Это стандарт для Discord voice

### Почему 3840 байт?

- 960 сэмплов × 2 байта (16-bit) × 2 (выравнивание) = 3840 байт
- Discord.py ожидает именно такой размер

### Формат аудио

- **Sample rate:** 48kHz
- **Bit depth:** 16-bit
- **Channels:** Mono
- **Format:** PCM

---

## ✅ Чеклист успешной настройки

- [ ] В логах: `samples=960` для каждого чанка
- [ ] В логах: `bytes=3840` для каждого чанка
- [ ] В логах: `Sent XXX chunks to Discord (XXXms of audio)`
- [ ] Звук в Discord нормальной скорости
- [ ] Звук не искажен
- [ ] Синхронизация с локальным TTS

---

## 🐛 Возможные проблемы

### Звук всё ещё слишком быстрый

**Проблема:** Чанки отправляются слишком быстро

**Решение:** Увеличьте задержку в `_send_to_discord`:
```python
if chunk_count % 10 == 0:
    time.sleep(0.05)  # 50ms вместо 10ms
```

### Звук прерывается

**Проблема:** Discord не успевает получать чанки

**Решение:** Уменьшите задержку или увеличьте размер буфера:
```python
# В StreamingAudioSource
self._audio_queue = queue.Queue(maxsize=200)  # Больше чанков в буфере
```

### Звук слишком медленный

**Проблема:** Слишком большая задержка

**Решение:** Уменьшите задержку:
```python
if chunk_count % 10 == 0:
    time.sleep(0.001)  # 1ms вместо 10ms
```

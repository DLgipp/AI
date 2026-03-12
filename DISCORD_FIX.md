# Discord Audio Streaming - Fix Applied

## ✅ Что было исправлено

### Проблема:
```
[TTS] Sending audio chunk to Discord: shape=(531000,), dtype=float32
[DISCORD_STREAM] Audio chunk received but streaming not active: active=False, source=False
```

Аудио отправляется из TTS, но Discord streaming не активен.

### Решение:

1. **Авто-запуск потока** - Теперь поток автоматически запускается при первом аудио чанке
2. **Убран ручной запуск** - Не нужно вызывать `start_audio_stream()` вручную
3. **Улучшена обработка состояний** - Лучшая обработка reconnect и voice state changes

---

## 🧪 Как тестировать

### 1. Запустите проект:

```bash
cd c:\AI
python main.py
```

### 2. Дождитесь подключения:

Ожидаемые логи:
```
[SYSTEM] [DISCORD] Discord bot logged in as YourBot#1234
[SYSTEM] [DISCORD_READY] Discord: Joined voice channel 987654321
[SYSTEM] [DISCORD_READY] Discord: Audio streaming will auto-start on first TTS
```

### 3. Скажите что-нибудь ассистенту

Когда ассистент начнёт говорить, вы должны увидеть:

```
[TTS] [LOCAL] TTS: Привет! Как дела?
[TTS] [DEBUG] Audio worker started, sample_rate=48000
[TTS] [DEBUG] Sending audio chunk to Discord: shape=(...), dtype=float32, chunk#1
[DISCORD_STREAM] [DEBUG] Auto-starting audio stream on first chunk
[SYSTEM] [DISCORD_STREAM] Audio stream started: volume=1.0
[DISCORD_STREAM] [DEBUG] Audio chunk sent to Discord: shape=(...)
[DISCORD_STREAM] [DEBUG] Audio chunk added to buffer: input_size=..., buffer_size=...
```

### 4. Проверьте звук в Discord

Вы должны слышать ответ ассистента в голосовом канале.

---

## 📊 Ключевые изменения в логах

### ✅ Успешный запуск:

```
[DISCORD_READY] Discord: Joined voice channel ...
[DISCORD_READY] Discord: Audio streaming will auto-start on first TTS
```

### ✅ Первый чанк (авто-старт):

```
[TTS] Sending audio chunk to Discord: shape=(...), chunk#1
[DISCORD_STREAM] Auto-starting audio stream on first chunk
[DISCORD_STREAM] Audio stream started: volume=1.0
[DISCORD_STREAM] Audio chunk sent to Discord: shape=(...)
```

### ✅ Последующие чанки:

```
[TTS] Sending audio chunk to Discord: shape=(...), chunk#2
[DISCORD_STREAM] Audio chunk sent to Discord: shape=(...)
[DISCORD_STREAM] Audio chunk added to buffer: input_size=..., buffer_size=...
```

---

## 🐛 Если всё ещё нет звука

### Проверка 1: Бот в канале?

Убедитесь что бот физически в голосовом канале Discord.

### Проверка 2: Авто-запуск сработал?

Ищите лог:
```
[DISCORD_STREAM] Auto-starting audio stream on first chunk
```

**Если нет:** Callback не срабатывает или бот не в канале.

### Проверка 3: Аудио отправляется?

Ищите:
```
[TTS] Sending audio chunk to Discord: shape=(...), chunk#1
```

**Если нет:** TTS не вызывает callback.

### Проверка 4: Громкость?

- Проверьте громкость бота в Discord (ПКМ на боте → Volume)
- Проверьте `DISCORD_DEFAULT_VOLUME = 1.0` в config.py

---

## 🔧 Debug режим

Для подробного логирования добавьте в `main.py`:

```python
import logging
logging.getLogger('discord').setLevel(logging.DEBUG)
```

---

## 📝 Примечания

- Поток запускается автоматически при первом аудио чанке
- Не нужно вызывать `start_audio_stream()` вручную
- При reconnect флаг сбрасывается и поток перезапустится автоматически

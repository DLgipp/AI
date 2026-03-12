# Discord Audio Streaming - Diagnostic Guide

## 🔍 Быстрая диагностика

### Шаг 1: Проверка конфигурации

Откройте `config.py` и проверьте:

```python
DISCORD_ENABLED = True  # Должно быть True
DISCORD_BOT_TOKEN = "YOUR_TOKEN_HERE"  # Не пустой!
DISCORD_GUILD_ID = 123456789  # Не 0!
DISCORD_VOICE_CHANNEL_ID = 987654321  # Не 0!
```

### Шаг 2: Запуск с логированием

```bash
cd c:\AI
python main.py
```

Смотрите логи. Ожидаемая последовательность:

```
[SYSTEM] [DISCORD_INIT] Initializing Discord voice client...
[SYSTEM] [DISCORD] Discord bot logged in as YourBot#1234
[DEBUG] [DISCORD] Discord TTS audio callback registered
[SYSTEM] [DISCORD_READY] Discord: Joined voice channel 987654321
[DEBUG] [DISCORD_INIT] Discord: TTS audio callback is SET
[SYSTEM] [DISCORD_READY] Discord: Audio streaming enabled
[SYSTEM] [DISCORD_READY] Discord: Streaming is ACTIVE
```

### Шаг 3: Проверка во время разговора

Когда ассистент говорит, вы должны видеть:

```
[TTS] [LOCAL] TTS: Привет! Как дела?
[TTS] [DEBUG] Audio worker started, sample_rate=48000
[TTS] [DEBUG] Sending audio chunk to Discord: shape=(...), dtype=float32
[DISCORD_STREAM] [DEBUG] Audio chunk sent to Discord: shape=(...)
[DISCORD_STREAM] [DEBUG] Audio chunk added to buffer: input_size=..., buffer_size=...
```

## 🐛 Если звука нет

### Проверка 1: Callback установлен?

Ищите лог:
```
[DEBUG] [DISCORD] Discord TTS audio callback registered
```

**Если нет:** Бот не подключился к Discord правильно.

### Проверка 2: Поток активен?

Ищите лог:
```
[SYSTEM] [DISCORD_READY] Discord: Streaming is ACTIVE
```

**Если нет:** `start_audio_stream()` не сработал.

### Проверка 3: Аудио отправляется?

Когда ассистент говорит, ищите:
```
[TTS] [DEBUG] Sending audio chunk to Discord: shape=(...), dtype=float32
[DISCORD_STREAM] [DEBUG] Audio chunk sent to Discord: shape=(...)
```

**Если нет:** TTS не вызывает callback.

### Проверка 4: Бот в канале?

Убедитесь что бот физически находится в голосовом канале.
- Посмотрите в Discord - должен быть виден бот в канале

## 🧪 Тестовый скрипт

Запустите тест:

```bash
python test_discord_audio.py
```

Это проверит:
1. ✅ Подключение к Discord
2. ✅ Вход в канал
3. ✅ Запуск потока
4. ✅ Отправку тестового аудио

## 📋 Чеклист

- [ ] `DISCORD_ENABLED = True`
- [ ] `DISCORD_BOT_TOKEN` установлен
- [ ] `DISCORD_GUILD_ID` и `DISCORD_VOICE_CHANNEL_ID` не 0
- [ ] Бот добавлен на сервер
- [ ] У бота есть права Connect и Speak
- [ ] В логах: "Discord TTS audio callback registered"
- [ ] В логах: "Streaming is ACTIVE"
- [ ] В логах: "Sending audio chunk to Discord"
- [ ] Бот в голосовом канале

## 💡 Решение проблем

### "Discord callback NOT SET"

Проблема: `on_ready()` не сработал до проверки.

Решение: Увеличьте задержку:
```python
await asyncio.sleep(3)  # Было 2
```

### "Streaming not active"

Проблема: Бот не в канале или ошибка при старте.

Решение: Проверьте логи `start_audio_stream()`.

### Аудио чанки отправляются, но звука нет

Возможные причины:
1. **Громкость Discord**: Проверьте громкость бота (ПКМ на боте → Volume)
2. **Неправильный формат**: Discord требует 48kHz, 16-bit PCM
3. **Бот не в том канале**: Убедитесь что вы в том же канале что и бот

### "Cannot start stream: not connected"

Проблема: Бот не подключился к голосовому каналу.

Решение:
```python
# Проверьте что канал существует и бот имеет права
# Попробуйте вручную переподключить:
await discord_client.leave_voice_channel()
await discord_client.join_voice_channel(GUILD_ID, CHANNEL_ID)
```

## 📞 Ещё нужна помощь?

Включите полное логирование Discord:

```python
# В main.py, перед discord_client.connect()
import logging
logging.getLogger('discord').setLevel(logging.DEBUG)
logging.getLogger('discord.voice_client').setLevel(logging.DEBUG)
```

Затем запустите ещё раз и посмотрите детальные логи.

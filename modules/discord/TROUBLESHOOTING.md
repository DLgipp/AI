# Discord Voice - Troubleshooting Guide

## 🐛 Нет звука в Discord

### Чеклист диагностики

#### 1. Проверка конфигурации

```python
# В config.py проверьте:
DISCORD_ENABLED = True
DISCORD_BOT_TOKEN = "ваш токен"  # Не пустой!
DISCORD_GUILD_ID = 123456789  # Не 0!
DISCORD_VOICE_CHANNEL_ID = 987654321  # Не 0!
```

#### 2. Проверка прав бота

Убедитесь что у бота есть права:
- ✅ Connect (Подключаться)
- ✅ Speak (Говорить)

Как проверить:
1. Откройте Discord Developer Portal
2. Ваше приложение → OAuth2 → URL Generator
3. В BOT PERMISSIONS выберите Connect и Speak
4. Перегенерируйте ссылку и пригласите бота снова

#### 3. Запуск теста

```bash
cd c:\AI
python test_discord_audio.py
```

Ожидаемый вывод:
```
============================================================
Discord Audio Stream Test
============================================================
✓ Конфигурация проверена
  Guild ID: 123456789
  Channel ID: 987654321
  Volume: 1.0

Подключение к Discord...
✓ Подключено к Discord
Вход в голосовой канал 987654321...
✓ В канале
Запуск аудио потока...
✓ Поток запущен
```

#### 4. Проверка логов

Ищите в логах:

```
[DISCORD] Discord bot logged in as YourBot#1234
[DISCORD] Discord TTS audio callback registered
[DISCORD_READY] Discord: Joined voice channel 987654321
[DISCORD_STREAM] Audio stream started: volume=1.0
[DISCORD_STREAM] Streaming is ACTIVE
[TTS] Sending audio chunk to Discord: shape=(...), dtype=float32
[DISCORD_STREAM] Audio chunk sent to Discord: shape=(...)
```

### Распространённые проблемы

#### ❌ "Discord callback not set"

**Проблема:** Callback не установлен до начала TTS

**Решение:**
1. Убедитесь что `on_ready()` сработал
2. Проверьте лог: `Discord TTS audio callback registered`
3. Добавьте задержку перед первым TTS

#### ❌ "Cannot start stream: not connected"

**Проблема:** Бот не в голосовом канале

**Решение:**
```python
# Проверьте подключение
if not discord_client.voice_client or not discord_client.voice_client.is_connected():
    print("Not connected to voice channel!")
```

#### ❌ "Audio chunk received but streaming not active"

**Проблема:** Поток не запущен или уже остановлен

**Решение:**
1. Проверьте что `start_audio_stream()` был вызван
2. Проверьте `_streaming_active = True`
3. Убедитесь что бот в канале

#### ❌ Тишина в Discord (но лог показывает отправку)

**Проблема:** Discord не получает аудио данные правильно

**Возможные причины:**

1. **Неправильный формат аудио:**
   - Discord ожидает 16-bit PCM
   - Sample rate: 48kHz
   - Chunk size: 3840 байт (20ms)

2. **Бот в неправильном канале:**
   - Проверьте что бот в том же канале что и вы

3. **Проблемы с громкостью:**
   - Проверьте громкость бота в Discord (правой кнопкой на боте → Volume)
   - Проверьте `DISCORD_DEFAULT_VOLUME = 1.0`

### Debug режим

Включите подробное логирование:

```python
# В main.py перед запуском
import logging
logging.getLogger('discord').setLevel(logging.DEBUG)
```

### Проверка потока

```python
# В любом месте после запуска
from modules.discord import get_voice_client

client = get_voice_client()
if client:
    print(f"Connected: {client.is_connected()}")
    print(f"Streaming active: {client._streaming_active}")
    print(f"Streaming source: {client._streaming_source is not None}")
    print(f"Voice client: {client.voice_client is not None}")
    if client.voice_client:
        print(f"Is playing: {client.voice_client.is_playing()}")
```

### Быстрый тест

```python
import asyncio
from modules.discord import DiscordVoiceClient
from config import DISCORD_BOT_TOKEN, DISCORD_GUILD_ID, DISCORD_VOICE_CHANNEL_ID

async def test():
    client = DiscordVoiceClient(
        token=DISCORD_BOT_TOKEN,
        guild_id=DISCORD_GUILD_ID,
        channel_id=DISCORD_VOICE_CHANNEL_ID
    )
    
    await client.connect()
    await asyncio.sleep(2)
    
    await client.join_voice_channel(DISCORD_GUILD_ID, DISCORD_VOICE_CHANNEL_ID)
    await asyncio.sleep(1)
    
    # Тестовый звук
    client.start_audio_stream()
    
    # Генерация тишины (проверка что поток работает)
    import numpy as np
    silence = np.zeros(4800, dtype=np.float32)  # 100ms тишины
    
    for i in range(10):  # 1 секунда
        client._streaming_source.add_audio_chunk(silence)
        await asyncio.sleep(0.1)
    
    client._streaming_source.mark_done()
    await asyncio.sleep(2)
    await client.disconnect()

asyncio.run(test())
```

## 📞 Контакты

Если проблема не решена:
1. Проверьте все логи
2. Запустите `test_discord_audio.py`
3. Проверьте права бота
4. Убедитесь что бот в том же канале что и вы

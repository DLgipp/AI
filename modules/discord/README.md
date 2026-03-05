# Discord Voice Integration Module

Модуль для подключения ИИ-ассистента к голосовым каналам Discord и вывода TTS (текст-в-речь) в войс чат.

## 📋 Содержание

- [Возможности](#возможности)
- [Установка](#установка)
- [Настройка](#настройка)
- [Быстрый старт](#быстрый-старт)
- [Использование](#использование)
- [API модуля](#api-модуля)
- [Интеграция с основным приложением](#интеграция-с-основным-приложением)
- [Примеры](#примеры)
- [Устранение неполадок](#устранение-неполадок)

---

## 🎯 Возможности

- **Подключение к Discord** - автоматическое подключение к серверу и голосовому каналу
- **TTS через Silero** - использование той же модели TTS, что и в основном приложении
- **Выразительная речь** - поддержка SSML для эмоциональной окраски речи
- **Очередь воспроизведения** - последовательное воспроизведение сообщений
- **Авто-переподключение** - автоматическое восстановление соединения при разрыве
- **Регулировка громкости** - настройка уровня громкости (0.0 - 2.0)
- **Асинхронная работа** - неблокирующее воспроизведение аудио

---

## 📦 Установка

### 1. Установка зависимостей

```bash
pip install -r modules/discord/requirements.txt
```

Или вручную:

```bash
pip install discord.py>=2.3.0
pip install discord.py[voice]>=2.3.0
pip install PyNaCl>=1.5.0
pip install scipy>=1.10.0
```

### 2. Создание Discord бота

1. Перейдите на [Discord Developer Portal](https://discord.com/developers/applications)
2. Нажмите "New Application" и создайте приложение
3. Перейдите в раздел "Bot"
4. Нажмите "Add Bot"
5. Скопируйте токен бота (DISCORD_BOT_TOKEN)

### 3. Приглашение бота на сервер

1. В разделе "OAuth2" → "URL Generator" выберите scopes: `bot`
2. Выберите permissions: `Connect`, `Speak`
3. Скопируйте сгенерированную ссылку и откройте в браузере
4. Выберите сервер для добавления бота

---

## ⚙️ Настройка

### Конфигурация в `config.py`

```python
# =========================
# DISCORD VOICE CONFIGURATION
# =========================
DISCORD_ENABLED = False  # Включить интеграцию с Discord
DISCORD_BOT_TOKEN = ""   # Токен бота из Discord Developer Portal
DISCORD_GUILD_ID = 0     # ID сервера (правой кнопкой на иконке → Copy ID)
DISCORD_VOICE_CHANNEL_ID = 0  # ID голосового канала (правой кнопкой → Copy ID)
DISCORD_DEFAULT_VOLUME = 1.0  # Громкость: 0.0 (тихо) до 2.0 (громко)
DISCORD_AUTO_RECONNECT = True  # Авто-переподключение при разрыве
DISCORD_USE_SSML = True  # Использовать SSML для выразительной речи
```

### Получение ID сервера и канала

1. В Discord включите режим разработчика:
   - Настройки пользователя → Дополнительно → Режим разработчика
   
2. Скопируйте ID:
   - **Сервер**: Правой кнопкой на иконке сервера → "Copy ID"
   - **Канал**: Правой кнопкой на голосовом канале → "Copy ID"

---

## 🚀 Быстрый старт

### Минимальный пример

```python
import asyncio
from modules.discord import init_discord_voice, speak, shutdown_discord_voice

async def main():
    # Инициализация и подключение
    await init_discord_voice(
        token="YOUR_BOT_TOKEN",
        guild_id=123456789,
        channel_id=987654321,
        volume=1.0
    )
    
    # Произнести фразу
    await speak("Привет! Я ИИ-ассистент в Discord!")
    
    # Подождать 2 секунды
    await asyncio.sleep(2)
    
    # Отключение
    await shutdown_discord_voice()

# Запуск
asyncio.run(main())
```

---

## 📖 Использование

### Базовое использование

```python
from modules.discord import DiscordVoiceClient, ExpressionContext

# Создание клиента
client = DiscordVoiceClient(
    token="YOUR_TOKEN",
    guild_id=123456789,
    channel_id=987654321,
    volume=1.0
)

# Подключение
await client.connect()

# Простое сообщение
await client.speak("Привет!")

# Сообщение с эмоциональной окраской
context = ExpressionContext(
    emotion="joy",
    emotional_tone="enthusiastic",
    engagement_level=0.8
)
await client.speak("Это потрясающая новость!", context=context, wait=True)

# Отключение
await client.disconnect()
```

### Очередь сообщений

```python
# Добавление в очередь (последовательное воспроизведение)
await client.speak_queue("Первое сообщение")
await client.speak_queue("Второе сообщение")
await client.speak_queue("Третье сообщение")
# Сообщения будут воспроизведены по порядку
```

### Управление громкостью

```python
# Установка громкости
client.set_volume(1.5)  # 150%

# Получение состояния
state = client.get_state()
print(f"Текущая громкость: {state['volume']}")
print(f"Воспроизводится: {state['playing']}")
```

### Проверка состояния

```python
# Подключен ли к Discord
if client.is_connected():
    print("Подключен к голосовому каналу")

# Воспроизводится ли аудио
if client.is_playing():
    print("Сейчас что-то говорю...")

# Полное состояние
state = client.get_state()
print(state)
# {
#     "connected": True,
#     "guild_id": 123456789,
#     "channel_id": 987654321,
#     "playing": False,
#     "volume": 1.0,
#     "queue_size": 0
# }
```

---

## 🔌 API модуля

### Класс DiscordVoiceClient

#### Конструктор

```python
client = DiscordVoiceClient(
    token: str,              # Токен Discord бота
    guild_id: Optional[int], # ID сервера (опционально)
    channel_id: Optional[int], # ID канала (опционально)
    volume: float = 1.0,     # Громкость (0.0 - 2.0)
    auto_reconnect: bool = True  # Авто-переподключение
)
```

#### Методы

| Метод | Описание |
|-------|----------|
| `async connect()` | Подключиться к Discord |
| `async disconnect()` | Отключиться от Discord |
| `async join_voice_channel(guild_id, channel_id)` | Войти в голосовой канал |
| `async leave_voice_channel()` | Выйти из голосового канала |
| `async speak(text, context, volume, wait)` | Произнести текст |
| `async speak_queue(text, context)` | Добавить в очередь |
| `is_connected()` | Проверка подключения |
| `is_playing()` | Проверка воспроизведения |
| `set_volume(volume)` | Установить громкость |
| `get_state()` | Получить состояние |

### Функции модуля

```python
# Получить глобальный экземпляр
client = get_voice_client()

# Инициализировать и подключить
await init_discord_voice(token, guild_id, channel_id, volume)

# Отключить
await shutdown_discord_voice()
```

### ExpressionContext (для выразительной речи)

```python
from modules.tts.tts_expression import ExpressionContext

context = ExpressionContext(
    emotion="joy",              # Эмоция: joy, sadness, anger, etc.
    emotional_tone="warm",      # Тон: warm, enthusiastic, empathetic
    decision_strategy="ANSWER_DIRECT",  # Стратегия ответа
    dominant_trait="curiosity",  # Черта личности
    engagement_level=0.8,       # Уровень вовлечённости (0-1)
    user_emotion="happy"        # Эмоция пользователя
)
```

---

## 🔗 Интеграция с основным приложением

### Пример интеграции с main.py

```python
# В main.py добавить:
from modules.discord import DiscordVoiceClient
from config import (
    DISCORD_ENABLED,
    DISCORD_BOT_TOKEN,
    DISCORD_GUILD_ID,
    DISCORD_VOICE_CHANNEL_ID,
    DISCORD_DEFAULT_VOLUME
)

# Глобальный клиент
discord_client: Optional[DiscordVoiceClient] = None

async def main():
    global discord_client
    
    # ... инициализация других компонентов ...
    
    # Инициализация Discord
    if DISCORD_ENABLED:
        discord_client = DiscordVoiceClient(
            token=DISCORD_BOT_TOKEN,
            guild_id=DISCORD_GUILD_ID,
            channel_id=DISCORD_VOICE_CHANNEL_ID,
            volume=DISCORD_DEFAULT_VOLUME
        )
        await discord_client.connect()
        log("Discord voice client initialized", role="SYSTEM")
    
    # ... остальной код ...
    
    # В llm_handler добавить вывод в Discord:
    async def llm_handler(event, dialog, silence_timer):
        # ... обработка через когнитивный пайплайн ...
        
        output = cognitive_pipeline.process_llm_response(...)
        final_text = output["text"]
        tts_context = output.get("tts_context")
        
        # Вывод в Discord
        if discord_client and discord_client.is_connected():
            from modules.tts.tts_expression import ExpressionContext
            context = ExpressionContext(**tts_context) if tts_context else None
            await discord_client.speak(final_text, context=context)
        
        # ... остальной код ...
```

### Полная интеграция с TTS циклом

```python
async def tts_loop_with_discord(dialog, silence_timer, discord_client, loop=None):
    """TTS цикл с выводом в Discord."""
    while True:
        assistant_msg = dialog.pop_next()
        
        if assistant_msg and assistant_msg["role"] == "assistant" and dialog.can_speak():
            dialog.set_speaking()
            
            tts_context = assistant_msg.get("tts_context")
            text = assistant_msg["text"]
            
            # Локальный TTS (если нужен)
            # await speak_async(text, silence_timer, context)
            
            # Discord TTS
            if discord_client and discord_client.is_connected():
                context = ExpressionContext(**tts_context) if tts_context else None
                await discord_client.speak(text, context=context)
            
            dialog.set_listening()
        
        await asyncio.sleep(0.02)

# В main():
await asyncio.gather(
    stt_loop(stt, loop),
    tts_loop_with_discord(dialog, silence_timer, discord_client, loop),
    silence_loop(silence_timer),
)
```

---

## 📚 Примеры

### Пример 1: Простое приветствие

```python
import asyncio
from modules.discord import init_discord_voice, speak, shutdown_discord_voice

async def greet():
    await init_discord_voice(
        token="YOUR_TOKEN",
        guild_id=123456789,
        channel_id=987654321
    )
    
    await speak("Привет! Добро пожаловать на сервер!")
    await asyncio.sleep(3)
    
    await shutdown_discord_voice()

asyncio.run(greet())
```

### Пример 2: Эмоциональный ответ

```python
from modules.discord import DiscordVoiceClient
from modules.tts.tts_expression import ExpressionContext

client = DiscordVoiceClient(token="...", guild_id=..., channel_id=...)
await client.connect()

# Радостное сообщение
joy_context = ExpressionContext(
    emotion="joy",
    emotional_tone="enthusiastic",
    engagement_level=0.9
)
await client.speak("Ура! Это потрясающая новость!", context=joy_context)

# Сочувствующее сообщение
empathy_context = ExpressionContext(
    emotion="sadness",
    emotional_tone="empathetic",
    engagement_level=0.7
)
await client.speak("Мне очень жаль, что так произошло...", context=empathy_context)

await client.disconnect()
```

### Пример 3: Очередь сообщений

```python
async def announce_sequence():
    client = get_voice_client()
    
    # Очередь объявлений
    await client.speak_queue("Внимание! Важное объявление.")
    await asyncio.sleep(1)
    await client.speak_queue("Через 5 минут начнётся мероприятие.")
    await client.speak_queue("Не пропустите!")
    
    # Ждём завершения очереди
    while client.is_playing() or client.get_state()["queue_size"] > 0:
        await asyncio.sleep(0.5)
```

### Пример 4: Реакция на сообщения в чате

```python
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    if 'привет' in message.content.lower():
        client = get_voice_client()
        if client and client.is_connected():
            await client.speak(f"Привет, {message.author.name}!")
    
    await bot.process_commands(message)
```

---

## 🐛 Устранение неполадок

### Бот не подключается к голосовому каналу

**Проблема**: Ошибка при подключении или бот не входит в канал

**Решения**:
1. Проверьте права доступа бота:
   - Убедитесь, что у бота есть права `Connect` и `Speak`
   - Проверьте, что бот имеет роль с доступом к каналу
   
2. Проверьте ID:
   - Убедитесь, что `DISCORD_GUILD_ID` и `DISCORD_VOICE_CHANNEL_ID` верны
   - ID должны быть числовыми, не строками

3. Проверьте токен:
   - Убедитесь, что токен бота действителен
   - Токен не должен содержать лишних пробелов

### ТTS не воспроизводится

**Проблема**: Бот подключен, но аудио не играет

**Решения**:
1. Проверьте установку PyNaCl:
   ```bash
   pip install PyNaCl>=1.5.0
   ```

2. Проверьте громкость:
   ```python
   client.set_volume(1.0)  # Установить 100%
   ```

3. Проверьте состояние:
   ```python
   state = client.get_state()
   print(f"Playing: {state['playing']}")
   ```

### Плохое качество аудио

**Проблема**: Аудио искажено или прерывается

**Решения**:
1. Уменьшите скорость генерации:
   - Добавьте задержку между сообщениями
   
2. Проверьте sample rate:
   - Silero использует 48000 Гц, Discord тоже
   - Убедитесь, что нет конфликта sample rates

3. Отключите SSML если есть проблемы:
   ```python
   DISCORD_USE_SSML = False
   ```

### Авто-переподключение не работает

**Проблема**: Бот не переподключается после разрыва

**Решения**:
1. Включите авто-переподключение:
   ```python
   DISCORD_AUTO_RECONNECT = True
   ```

2. Проверьте логи:
   - Ищите сообщения "Auto-reconnecting to voice channel"
   - Проверьте права доступа после перезапуска

---

## 📝 Лицензия

Модуль создан для образовательных и исследовательских целей.

---

## 🤝 Поддержка

Вопросы и предложения направляйте через Issues на GitHub.

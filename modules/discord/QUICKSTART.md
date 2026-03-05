# Discord Voice Integration - Quick Start Guide

## 🚀 Быстрая настройка за 5 минут

### Шаг 1: Установка зависимостей

```bash
cd c:\AI
pip install -r modules/discord/requirements.txt
```

Или по отдельности:

```bash
pip install discord.py>=2.3.0
pip install discord.py[voice]>=2.3.0
pip install PyNaCl>=1.5.0
pip install scipy>=1.10.0
```

---

### Шаг 2: Создание Discord бота

1. **Откройте [Discord Developer Portal](https://discord.com/developers/applications)**

2. **Создайте приложение:**
   - Нажмите кнопку "New Application"
   - Введите имя (например, "AI Assistant")
   - Нажмите "Create"

3. **Создайте бота:**
   - В левом меню выберите "Bot"
   - Нажмите "Add Bot" → "Yes, do it!"
   - Скопируйте токен (кнопка "Reset Token" или "View Token")
   - **Сохраните токен!** (вставьте в `config.py`)

4. **Настройте права:**
   - В разделе "Privileged Gateway Intents" включите:
     - ✅ MESSAGE CONTENT INTENT
     - ✅ SERVER MEMBERS INTENT (опционально)

---

### Шаг 3: Приглашение бота на сервер

1. **Сгенерируйте ссылку-приглашение:**
   - В левом меню: "OAuth2" → "URL Generator"
   - В "SCOPES" выберите: ✅ `bot`
   - В "BOT PERMISSIONS" выберите:
     - ✅ Connect
     - ✅ Speak
     - ✅ Send Messages (для текстовых команд)

2. **Скопируйте ссылку:**
   - Скопируйте сгенерированную URL внизу
   - Откройте в браузере
   - Выберите сервер для добавления
   - Нажмите "Authorize"

---

### Шаг 4: Получение ID сервера и канала

1. **Включите режим разработчика в Discord:**
   - Настройки пользователя (шестерёнка внизу слева)
   - "Дополнительно" → включите "Режим разработчика"

2. **Скопируйте ID сервера:**
   - Правой кнопкой на иконке сервера (слева)
   - Нажмите "Copy ID"
   - Вставьте в `config.py` → `DISCORD_GUILD_ID`

3. **Скопируйте ID голосового канала:**
   - Правой кнопкой на голосовом канале
   - Нажмите "Copy ID"
   - Вставьте в `config.py` → `DISCORD_VOICE_CHANNEL_ID`

---

### Шаг 5: Настройка config.py

Откройте `config.py` и заполните:

```python
# =========================
# DISCORD VOICE CONFIGURATION
# =========================
DISCORD_ENABLED = True  # Включить Discord
DISCORD_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Вставьте токен
DISCORD_GUILD_ID = 123456789012345678  # Вставьте ID сервера
DISCORD_VOICE_CHANNEL_ID = 987654321098765432  # Вставьте ID канала
DISCORD_DEFAULT_VOLUME = 1.0  # Громкость (0.0 - 2.0)
DISCORD_AUTO_RECONNECT = True  # Авто-переподключение
DISCORD_USE_SSML = True  # Выразительная речь
```

---

### Шаг 6: Проверка работы

#### Тестовый запуск:

```bash
cd c:\AI
python modules/discord/example.py
```

Если всё настроено правильно:
- Бот подключится к Discord
- Войдёт в голосовой канал
- Произнесёт тестовые фразы

---

## 🎯 Интеграция с основным приложением

### Вариант 1: Простая интеграция

Добавьте в `main.py`:

```python
from modules.discord import DiscordVoiceClient
from config import DISCORD_ENABLED, DISCORD_BOT_TOKEN, DISCORD_GUILD_ID, DISCORD_VOICE_CHANNEL_ID

# Глобальный клиент
discord_client = None

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
    
    # ... остальной код ...
```

### Вариант 2: Полная интеграция с TTS

Замените `tts_loop` в `main.py`:

```python
from modules.discord import get_voice_client

async def tts_loop_with_discord(dialog, silence_timer, discord_client, loop=None):
    """TTS цикл с выводом в Discord."""
    while True:
        assistant_msg = dialog.pop_next()
        
        if assistant_msg and assistant_msg["role"] == "assistant" and dialog.can_speak():
            dialog.set_speaking()
            
            text = assistant_msg["text"]
            tts_context = assistant_msg.get("tts_context")
            
            # Discord TTS
            if discord_client and discord_client.is_connected():
                from modules.tts.tts_expression import ExpressionContext
                context = ExpressionContext(**tts_context) if tts_context else None
                await discord_client.speak(text, context=context)
            
            dialog.set_listening()
        
        await asyncio.sleep(0.02)
```

---

## 🐛 Решение проблем

### Ошибка: "Discord is not configured"

**Проблема:** Не заполнен `config.py`

**Решение:**
```python
DISCORD_ENABLED = True
DISCORD_BOT_TOKEN = "ваш токен"
DISCORD_GUILD_ID = 123456789
DISCORD_VOICE_CHANNEL_ID = 987654321
```

### Ошибка: "Invalid token"

**Проблема:** Неверный токен бота

**Решение:**
1. Проверьте, что скопировали токен без лишних пробелов
2. Убедитесь, что токен действителен (пересоздайте в Discord Developer Portal)

### Ошибка: "Guild not found" или "Channel not found"

**Проблема:** Неверные ID сервера или канала

**Решение:**
1. Убедитесь, что бот добавлен на сервер
2. Перепроверьте ID (правой кнопкой → Copy ID)
3. Убедитесь, что бот имеет доступ к каналу

### Ошибка: "PyNaCl not installed"

**Проблема:** Не установлена библиотека для работы с аудио

**Решение:**
```bash
pip install PyNaCl>=1.5.0
```

### Бот подключается, но молчит

**Проблема:** ТTS не воспроизводится

**Решение:**
1. Проверьте громкость: `client.set_volume(1.0)`
2. Проверьте состояние: `print(client.get_state())`
3. Попробуйте простой тест:
   ```python
   await client.speak("Тест", wait=True)
   ```

### Бот вылетает из канала

**Проблема:** Разрыв соединения

**Решение:**
1. Включите авто-переподключение:
   ```python
   DISCORD_AUTO_RECONNECT = True
   ```
2. Проверьте стабильность интернет-соединения
3. Убедитесь, что у бота есть права на канал

---

## 📚 Дополнительные ресурсы

- **Документация модуля:** `modules/discord/README.md`
- **Примеры кода:** `modules/discord/example.py`
- **Discord.py docs:** https://discordpy.readthedocs.io/
- **Discord API:** https://discord.com/developers/docs/intro

---

## ✅ Чеклист успешной настройки

- [ ] Установлены зависимости (`discord.py`, `PyNaCl`, `scipy`)
- [ ] Создан бот в Discord Developer Portal
- [ ] Скопирован токен бота
- [ ] Бот добавлен на сервер
- [ ] Включён MESSAGE CONTENT INTENT
- [ ] Получены ID сервера и канала
- [ ] Заполнен `config.py`
- [ ] Тестовый запуск успешен
- [ ] Бот говорит в голосовом канале

---

**Готово!** 🎉 Теперь ваш ИИ-ассистент может говорить в Discord!

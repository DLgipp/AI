"""
Discord Audio Stream Test

Проверка работы аудио потока в Discord.
Запустите этот скрипт для тестирования.

Перед запуском:
1. Убедитесь что DISCORD_ENABLED=True в config.py
2. Заполните DISCORD_BOT_TOKEN, DISCORD_GUILD_ID, DISCORD_VOICE_CHANNEL_ID
3. Бот должен быть добавлен на сервер
"""

import asyncio
import sys

# Добавляем путь к модулям
sys.path.insert(0, 'c:\\AI')

from config import (
    DISCORD_ENABLED,
    DISCORD_BOT_TOKEN,
    DISCORD_GUILD_ID,
    DISCORD_VOICE_CHANNEL_ID,
    DISCORD_DEFAULT_VOLUME,
)
from modules.discord import DiscordVoiceClient
from modules.stt.logger import log


async def test_discord_audio():
    """Тестирование аудио потока в Discord."""
    
    print("=" * 60)
    print("Discord Audio Stream Test")
    print("=" * 60)
    
    # Проверка конфигурации
    if not DISCORD_ENABLED:
        print("❌ DISCORD_ENABLED=False в config.py")
        return
    
    if not DISCORD_BOT_TOKEN:
        print("❌ DISCORD_BOT_TOKEN не установлен")
        return
    
    if not DISCORD_GUILD_ID or not DISCORD_VOICE_CHANNEL_ID:
        print("❌ DISCORD_GUILD_ID или DISCORD_VOICE_CHANNEL_ID не установлены")
        return
    
    print(f"✓ Конфигурация проверена")
    print(f"  Guild ID: {DISCORD_GUILD_ID}")
    print(f"  Channel ID: {DISCORD_VOICE_CHANNEL_ID}")
    print(f"  Volume: {DISCORD_DEFAULT_VOLUME}")
    print()
    
    # Создание клиента
    client = DiscordVoiceClient(
        token=DISCORD_BOT_TOKEN,
        guild_id=DISCORD_GUILD_ID,
        channel_id=DISCORD_VOICE_CHANNEL_ID,
        volume=DISCORD_DEFAULT_VOLUME,
        auto_reconnect=True
    )
    
    try:
        # Подключение
        print("Подключение к Discord...")
        await client.connect()
        print("✓ Подключено к Discord")
        await asyncio.sleep(2)
        
        # Вход в канал
        print(f"Вход в голосовой канал {DISCORD_VOICE_CHANNEL_ID}...")
        success = await client.join_voice_channel(
            DISCORD_GUILD_ID,
            DISCORD_VOICE_CHANNEL_ID
        )
        
        if not success:
            print("❌ Не удалось войти в канал")
            return
        
        print("✓ В канале")
        await asyncio.sleep(1)
        
        # Запуск потока
        print("Запуск аудио потока...")
        success = client.start_audio_stream()
        
        if not success:
            print("❌ Не удалось запустить поток")
            return
        
        print("✓ Поток запущен")
        print()
        print("=" * 60)
        print("ТЕСТ 1: Проверка callback")
        print("=" * 60)
        
        # Проверяем что callback установлен
        from modules.tts.tts import get_discord_audio_callback
        callback = get_discord_audio_callback()
        
        if callback:
            print("✓ Audio callback установлен")
        else:
            print("❌ Audio callback НЕ установлен!")
        
        print()
        print("=" * 60)
        print("ТЕСТ 2: Отправка тестового аудио")
        print("=" * 60)
        
        # Генерируем тестовое аудио
        import numpy as np
        from modules.tts.tts import model, sample_rate, speaker
        
        print("Генерация тестового аудио...")
        test_text = "Привет! Это тестовое сообщение для Discord."
        
        audio = model.apply_tts(
            text=test_text,
            speaker=speaker,
            sample_rate=sample_rate
        )
        
        audio_array = np.array(audio, dtype=np.float32)
        print(f"✓ Аудио сгенерировано: размер={len(audio_array)}, duration={len(audio_array)/sample_rate:.2f}s")
        
        # Отправляем в поток
        print("Отправка в Discord...")
        
        if client._streaming_source:
            # Разбиваем на чанки
            chunk_size = 960  # 20ms при 48kHz
            chunks = []
            
            for i in range(0, len(audio_array), chunk_size):
                chunk = audio_array[i:i+chunk_size]
                chunks.append(chunk)
            
            print(f"Разбито на {len(chunks)} чанков")
            
            # Отправляем чанки
            for i, chunk in enumerate(chunks):
                client._streaming_source.add_audio_chunk(chunk)
                if i % 50 == 0:
                    print(f"Отправлено чанков: {i}/{len(chunks)}")
                await asyncio.sleep(0.001)  # Небольшая задержка
            
            # Завершаем поток
            client._streaming_source.mark_done()
            print("✓ Отправка завершена")
            
            # Ждём воспроизведения
            print("Ожидание воспроизведения...")
            await asyncio.sleep(len(audio_array) / sample_rate + 2)
            
        else:
            print("❌ Streaming source не создан!")
        
        print()
        print("=" * 60)
        print("Тест завершен!")
        print("Вы должны были услышать: 'Привет! Это тестовое сообщение для Discord.'")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Очистка
        print("\nОтключение...")
        if client:
            await client.disconnect()
        print("✓ Отключено")


if __name__ == "__main__":
    asyncio.run(test_discord_audio())

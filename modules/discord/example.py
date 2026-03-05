"""
Discord Voice Integration Example

This example demonstrates how to integrate the AI assistant with Discord voice channels.

Prerequisites:
1. Install dependencies: pip install -r modules/discord/requirements.txt
2. Create a Discord bot at https://discord.com/developers/applications
3. Get bot token and server/channel IDs
4. Update config.py with your Discord credentials

Usage:
    python modules/discord/example.py
"""

import asyncio
import os
from typing import Optional

# Import Discord module
from modules.discord import (
    DiscordVoiceClient,
    init_discord_voice,
    shutdown_discord_voice,
    get_voice_client
)

# Import TTS expression context for emotional speech
from modules.tts.tts_expression import ExpressionContext

# Import from config
from config import (
    DISCORD_ENABLED,
    DISCORD_BOT_TOKEN,
    DISCORD_GUILD_ID,
    DISCORD_VOICE_CHANNEL_ID,
    DISCORD_DEFAULT_VOLUME
)


async def example_basic():
    """Basic example: connect, speak, disconnect."""
    print("\n=== Basic Example ===")
    
    client = DiscordVoiceClient(
        token=DISCORD_BOT_TOKEN,
        guild_id=DISCORD_GUILD_ID,
        channel_id=DISCORD_VOICE_CHANNEL_ID,
        volume=DISCORD_DEFAULT_VOLUME
    )
    
    try:
        # Connect
        await client.connect()
        print("Connected to Discord")
        await asyncio.sleep(1)
        
        # Speak
        await client.speak("Привет! Я ИИ-ассистент в Discord!", wait=True)
        print("Spoke greeting")
        await asyncio.sleep(1)
        
        # Check state
        state = client.get_state()
        print(f"State: {state}")
        
    finally:
        # Disconnect
        await client.disconnect()
        print("Disconnected from Discord")


async def example_emotional_speech():
    """Example with emotional/expressive speech using SSML."""
    print("\n=== Emotional Speech Example ===")
    
    client = DiscordVoiceClient(
        token=DISCORD_BOT_TOKEN,
        guild_id=DISCORD_GUILD_ID,
        channel_id=DISCORD_VOICE_CHANNEL_ID,
        volume=DISCORD_DEFAULT_VOLUME
    )
    
    await client.connect()
    
    try:
        # Happy message
        print("Speaking: Joyful message")
        joy_context = ExpressionContext(
            emotion="joy",
            emotional_tone="enthusiastic",
            engagement_level=0.9,
            dominant_trait="extraversion"
        )
        await client.speak(
            "Ура! Это потрясающая новость! Я так рад!",
            context=joy_context,
            wait=True
        )
        await asyncio.sleep(1)
        
        # Empathetic message
        print("Speaking: Empathetic message")
        empathy_context = ExpressionContext(
            emotion="sadness",
            emotional_tone="empathetic",
            engagement_level=0.7,
            dominant_trait="empathy"
        )
        await client.speak(
            "Мне очень жаль, что так произошло. Я понимаю твои чувства.",
            context=empathy_context,
            wait=True
        )
        await asyncio.sleep(1)
        
        # Curious message
        print("Speaking: Curious message")
        curiosity_context = ExpressionContext(
            emotion="neutral",
            emotional_tone="warm",
            engagement_level=0.8,
            dominant_trait="curiosity"
        )
        await client.speak(
            "Интересно... А что ты думаешь об этом? Расскажи подробнее!",
            context=curiosity_context,
            wait=True
        )
        
    finally:
        await client.disconnect()


async def example_queued_speech():
    """Example with queued speech (sequential playback)."""
    print("\n=== Queued Speech Example ===")
    
    client = DiscordVoiceClient(
        token=DISCORD_BOT_TOKEN,
        guild_id=DISCORD_GUILD_ID,
        channel_id=DISCORD_VOICE_CHANNEL_ID,
        volume=DISCORD_DEFAULT_VOLUME
    )
    
    await client.connect()
    
    try:
        # Queue multiple messages
        print("Queueing messages...")
        await client.speak_queue("Внимание! Важное объявление.")
        await client.speak_queue("Через несколько минут начнётся мероприятие.")
        await client.speak_queue("Пожалуйста, подготовьтесь и не пропустите!")
        await client.speak_queue("Спасибо за внимание!")
        
        # Wait for queue to finish
        print("Waiting for queue to finish...")
        while client.is_playing() or client.get_state()["queue_size"] > 0:
            await asyncio.sleep(0.5)
        
        print("Queue finished!")
        
    finally:
        await client.disconnect()


async def example_volume_control():
    """Example with volume control."""
    print("\n=== Volume Control Example ===")
    
    client = DiscordVoiceClient(
        token=DISCORD_BOT_TOKEN,
        guild_id=DISCORD_GUILD_ID,
        channel_id=DISCORD_VOICE_CHANNEL_ID,
        volume=0.5  # Start at 50%
    )
    
    await client.connect()
    
    try:
        # Speak at 50% volume
        print("Speaking at 50% volume")
        await client.speak("Тихое сообщение...", wait=True)
        
        # Increase to 100%
        client.set_volume(1.0)
        print("Speaking at 100% volume")
        await client.speak("Нормальное сообщение!", wait=True)
        
        # Increase to 150%
        client.set_volume(1.5)
        print("Speaking at 150% volume")
        await client.speak("ГРОМКОЕ СООБЩЕНИЕ!", wait=True)
        
        # Check state
        state = client.get_state()
        print(f"Final volume: {state['volume']}")
        
    finally:
        await client.disconnect()


async def example_reconnect():
    """Example with auto-reconnect."""
    print("\n=== Auto-Reconnect Example ===")
    
    client = DiscordVoiceClient(
        token=DISCORD_BOT_TOKEN,
        guild_id=DISCORD_GUILD_ID,
        channel_id=DISCORD_VOICE_CHANNEL_ID,
        auto_reconnect=True  # Enable auto-reconnect
    )
    
    await client.connect()
    
    try:
        print("Connected with auto-reconnect enabled")
        print("If disconnected, bot will try to reconnect automatically")
        
        # Monitor connection
        for i in range(10):
            state = client.get_state()
            print(f"State check {i+1}: connected={state['connected']}")
            await asyncio.sleep(2)
        
    finally:
        await client.disconnect()


async def example_integration_with_cognitive_pipeline():
    """
    Example: Integration with cognitive pipeline.
    
    This shows how to use Discord voice with the full AI assistant pipeline.
    """
    print("\n=== Cognitive Pipeline Integration Example ===")
    
    # Import cognitive pipeline
    from modules.cognitive_pipeline import CognitivePipeline
    from config import ASSISTANT_NAME, DEFAULT_SESSION_ID, DEFAULT_USER_ID
    
    # Initialize Discord
    client = DiscordVoiceClient(
        token=DISCORD_BOT_TOKEN,
        guild_id=DISCORD_GUILD_ID,
        channel_id=DISCORD_VOICE_CHANNEL_ID
    )
    await client.connect()
    
    # Initialize cognitive pipeline
    pipeline = CognitivePipeline(
        session_id=DEFAULT_SESSION_ID,
        user_id=DEFAULT_USER_ID,
        assistant_name=ASSISTANT_NAME
    )
    
    try:
        # Simulate user input
        user_text = "Привет! Расскажи что-нибудь интересное!"
        print(f"Processing: {user_text}")
        
        # Process through cognitive pipeline
        result = await pipeline.process(
            text=user_text,
            voice_features=None,
            silence_duration=5.0
        )
        
        # Get response from LLM (simulate)
        llm_response = "Привет! Я очень рада тебя видеть! Знаешь ли ты, что осьминоги имеют три сердца?"
        
        # Process LLM response
        output = pipeline.process_llm_response(
            llm_response=llm_response,
            pipeline_result=result
        )
        
        # Speak in Discord with emotional context
        tts_context = output.get("tts_context")
        context = ExpressionContext(**tts_context) if tts_context else None
        
        print(f"Speaking in Discord: {output['text']}")
        await client.speak(output["text"], context=context, wait=True)
        
        # Get pipeline statistics
        stats = pipeline.get_statistics()
        print(f"Personality: {stats['personality']['dominant_trait']}")
        print(f"Mood: {stats['personality']['current_mood_valence']:+.2f}")
        
    finally:
        await client.disconnect()


async def run_all_examples():
    """Run all examples sequentially."""
    print("=" * 60)
    print("Discord Voice Integration Examples")
    print("=" * 60)
    
    # Check if Discord is configured
    if not DISCORD_ENABLED or not DISCORD_BOT_TOKEN:
        print("\n⚠️  Discord is not configured!")
        print("Please set DISCORD_ENABLED=True and DISCORD_BOT_TOKEN in config.py")
        return
    
    # Run examples
    examples = [
        ("Basic", example_basic),
        ("Emotional Speech", example_emotional_speech),
        ("Queued Speech", example_queued_speech),
        ("Volume Control", example_volume_control),
        ("Auto-Reconnect", example_reconnect),
        ("Cognitive Pipeline", example_integration_with_cognitive_pipeline),
    ]
    
    for name, example_func in examples:
        try:
            await example_func()
            await asyncio.sleep(2)
        except Exception as e:
            print(f"\n❌ Example '{name}' failed: {e}")
            await asyncio.sleep(1)
    
    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    # Run examples
    asyncio.run(run_all_examples())
    
    # Or run specific example:
    # asyncio.run(example_basic())
    # asyncio.run(example_emotional_speech())

"""
Discord Module - Voice channel integration for TTS output

This module provides Discord voice channel integration,
allowing the AI assistant to speak responses in Discord voice chat.

Quick Start:
    from modules.discord import init_discord_voice, speak

    # Initialize
    await init_discord_voice(
        token="YOUR_BOT_TOKEN",
        guild_id=123456789,
        channel_id=987654321
    )

    # Audio streaming (TTS audio is automatically streamed to Discord)
    client.start_audio_stream()

Modules:
    - voice_client: Discord voice client with TTS support and audio streaming
"""

from .voice_client import (
    DiscordVoiceClient,
    VoiceChannelConfig,
    TTSAudioSource,
    AudioSource,
    StreamingAudioSource,
    init_discord_voice,
    shutdown_discord_voice,
    get_voice_client
)

__all__ = [
    "DiscordVoiceClient",
    "VoiceChannelConfig",
    "TTSAudioSource",
    "AudioSource",
    "StreamingAudioSource",
    "init_discord_voice",
    "shutdown_discord_voice",
    "get_voice_client"
]

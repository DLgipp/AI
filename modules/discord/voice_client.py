"""
Discord Voice Module - TTS output to Discord voice channels

This module provides integration with Discord voice channels,
allowing the AI assistant to speak TTS responses in voice chat.

Features:
- Connect/join Discord voice channels
- Stream TTS audio using Silero model
- Support for expressive speech (SSML)
- Audio queue management
- Integration with cognitive pipeline

Usage:
    from modules.discord.voice_client import DiscordVoiceClient
    
    client = DiscordVoiceClient(token="YOUR_BOT_TOKEN")
    await client.connect()
    await client.join_voice_channel(guild_id, channel_id)
    await client.speak("Hello from AI assistant!")
"""

import asyncio
import io
import logging
import threading
import queue
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass

import discord
from discord.ext import commands
import numpy as np

from modules.tts.tts import model, sample_rate, speaker, set_discord_audio_callback, get_discord_audio_callback
from modules.tts.tts_expression import ExpressionContext, convert_to_ssml
from modules.stt.logger import log

# Configure discord.py logging
discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.INFO)


@dataclass
class VoiceChannelConfig:
    """Configuration for voice channel connection."""
    guild_id: int
    channel_id: int
    
    @classmethod
    def from_env(cls, guild_id: int, channel_id: int) -> 'VoiceChannelConfig':
        return cls(guild_id=guild_id, channel_id=channel_id)


class AudioSource(discord.AudioSource):
    """
    Custom audio source for streaming TTS audio.
    
    Provides PCM audio data to Discord's voice client.
    """
    
    def __init__(self, audio_data: np.ndarray, sample_rate: int = 48000):
        """
        Initialize audio source.
        
        Args:
            audio_data: Numpy array with audio samples (float32, -1 to 1)
            sample_rate: Sample rate in Hz (default 48000 for Discord)
        """
        self.audio_data = audio_data
        self.sample_rate = sample_rate
        self.position = 0
        self._volume = 1.0
        
        # Resample if needed (Discord expects 48kHz)
        if sample_rate != 48000:
            from scipy import signal
            num_samples = int(len(audio_data) * 48000 / sample_rate)
            self.audio_data = signal.resample(audio_data, num_samples).astype(np.float32)
            self.sample_rate = 48000
        
        # Convert to 16-bit PCM
        self.pcm_data = (self.audio_data * 32767).astype(np.int16)
        
    def read(self) -> bytes:
        """Read next chunk of audio data."""
        chunk_size = 3840  # 20ms at 48kHz, 16-bit, mono
        start = self.position
        end = min(start + chunk_size, len(self.pcm_data))
        
        if start >= len(self.pcm_data):
            return b''
        
        chunk = self.pcm_data[start:end]
        self.position = end
        
        # Apply volume
        if self._volume != 1.0:
            chunk = (chunk * self._volume).astype(np.int16)
        
        return chunk.tobytes()
    
    def is_done(self) -> bool:
        """Check if audio playback is complete."""
        return self.position >= len(self.pcm_data)
    
    @property
    def volume(self) -> float:
        """Get current volume level."""
        return self._volume
    
    @volume.setter
    def volume(self, value: float):
        """Set volume level (0.0 to 2.0)."""
        self._volume = max(0.0, min(2.0, value))
    
    def cleanup(self):
        """Cleanup resources."""
        pass


class StreamingAudioSource(AudioSource):
    """
    Streaming audio source that receives audio chunks in real-time.

    Used for streaming TTS audio directly from the TTS module.
    TTS sends chunks of 960 samples (20ms at 48kHz).
    
    Discord expects: 960 samples × 2 bytes (16-bit) × 2 channels = 3840 bytes
    """

    def __init__(self, sample_rate: int = 48000):
        """
        Initialize streaming audio source.

        Args:
            sample_rate: Sample rate in Hz (default 48000 for Discord)
        """
        self.sample_rate = sample_rate
        self._volume = 1.0
        self._audio_queue = queue.Queue()
        self._done = False
        # Discord expects: 960 samples × 2 bytes × 2 channels = 3840 bytes
        self._discord_frame_size = 3840

    def add_audio_chunk(self, audio_data: np.ndarray):
        """
        Add audio chunk to the stream.

        Args:
            audio_data: Numpy array with audio samples (float32, -1 to 1), expected 960 samples mono
        """
        try:
            # Convert to 16-bit PCM
            pcm_chunk = (audio_data * 32767).astype(np.int16)
            
            # Apply volume
            if self._volume != 1.0:
                pcm_chunk = (pcm_chunk * self._volume).astype(np.int16)

            # Convert mono to stereo by interleaving
            # Each sample is duplicated for left and right channels
            stereo_chunk = np.empty(len(pcm_chunk) * 2, dtype=np.int16)
            stereo_chunk[0::2] = pcm_chunk  # Left channel
            stereo_chunk[1::2] = pcm_chunk  # Right channel
            
            stereo_bytes = stereo_chunk.tobytes()
            
            # Ensure correct size
            if len(stereo_bytes) != self._discord_frame_size:
                log(f"Warning: Expected {self._discord_frame_size} bytes, got {len(stereo_bytes)}",
                    role="WARN", stage="DISCORD_STREAM")
            
            # Add to queue
            self._audio_queue.put(stereo_bytes)
            
            log(f"Audio chunk added: mono_samples={len(audio_data)}, stereo_bytes={len(stereo_bytes)}, queue_size={self._audio_queue.qsize()}",
                role="DEBUG", stage="DISCORD_STREAM")

        except Exception as e:
            log(f"Error adding audio chunk: {e}",
                role="ERROR", stage="DISCORD_STREAM")
            import traceback
            log(traceback.format_exc(), role="ERROR", stage="DISCORD_STREAM")

    def mark_done(self):
        """Mark stream as complete."""
        self._done = True

    def read(self) -> bytes:
        """Read next chunk of audio data (fixed size for Discord)."""
        try:
            # Try to get data from queue
            chunk = self._audio_queue.get(timeout=0.05)
            return chunk
        except queue.Empty:
            # Return silence if no data
            if self._done and self._audio_queue.empty():
                return b''
            return b'\x00' * self._discord_frame_size

    def is_done(self) -> bool:
        """Check if audio playback is complete."""
        return self._done and self._audio_queue.empty()

    @property
    def volume(self) -> float:
        """Get current volume level."""
        return self._volume

    @volume.setter
    def volume(self, value: float):
        """Set volume level (0.0 to 2.0)."""
        self._volume = max(0.0, min(2.0, value))

    def cleanup(self):
        """Cleanup resources."""
        self._audio_queue.queue.clear()
        self._done = True


class TTSAudioSource(AudioSource):
    """
    Audio source that generates TTS audio on-the-fly.
    
    Supports SSML for expressive speech.
    """
    
    def __init__(
        self,
        text: str,
        use_ssml: bool = True,
        context: Optional[ExpressionContext] = None,
        sample_rate: int = 48000
    ):
        """
        Initialize TTS audio source.
        
        Args:
            text: Text to synthesize
            use_ssml: Whether to use SSML for expression
            context: Emotional context for SSML
            sample_rate: Output sample rate
        """
        self.text = text
        self.use_ssml = use_ssml
        self.context = context
        self.audio_data = self._generate_audio()
        super().__init__(self.audio_data, sample_rate)
    
    def _generate_audio(self) -> np.ndarray:
        """Generate audio from text."""
        try:
            # Try SSML first
            if self.use_ssml and self.context:
                ssml_text = convert_to_ssml(
                    text=self.text,
                    emotion=self.context.emotion,
                    emotional_tone=self.context.emotional_tone,
                    decision_strategy=self.context.decision_strategy,
                    dominant_trait=self.context.dominant_trait,
                    engagement_level=self.context.engagement_level,
                    user_emotion=self.context.user_emotion,
                    validate=True,
                    repair=True
                )
                
                if ssml_text != self.text:
                    log(f"Discord TTS: Using SSML, len={len(ssml_text)}",
                        role="DEBUG", stage="DISCORD")
                    audio = model.apply_tts(
                        ssml_text=ssml_text,
                        speaker=speaker,
                        sample_rate=sample_rate
                    )
                    return np.array(audio, dtype=np.float32)
            
            # Fallback to plain text
            log(f"Discord TTS: Using plain text, len={len(self.text)}",
                role="DEBUG", stage="DISCORD")
            audio = model.apply_tts(
                text=self.text,
                speaker=speaker,
                sample_rate=sample_rate
            )
            return np.array(audio, dtype=np.float32)
            
        except Exception as e:
            log(f"Discord TTS generation error: {e}",
                role="ERROR", stage="DISCORD")
            # Return silent audio on error
            return np.zeros(sample_rate, dtype=np.float32)


class DiscordVoiceClient:
    """
    Discord voice client for TTS output.
    
    Manages connection to Discord and voice channel operations.
    """
    
    def __init__(
        self,
        token: str,
        guild_id: Optional[int] = None,
        channel_id: Optional[int] = None,
        volume: float = 1.0,
        auto_reconnect: bool = True
    ):
        """
        Initialize Discord voice client.
        
        Args:
            token: Discord bot token
            guild_id: Default guild ID to connect to
            channel_id: Default voice channel ID
            volume: Default volume level (0.0 to 2.0)
            auto_reconnect: Auto-reconnect on disconnect
        """
        self.token = token
        self.default_guild_id = guild_id
        self.default_channel_id = channel_id
        self.default_volume = volume
        self.auto_reconnect = auto_reconnect
        
        # Bot instance
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        self.bot = commands.Bot(command_prefix='!', intents=intents)
        
        # Voice state
        self.voice_client: Optional[discord.VoiceClient] = None
        self.current_guild_id: Optional[int] = None
        self.current_channel_id: Optional[int] = None
        self._connected = False
        self._audio_queue: asyncio.Queue = asyncio.Queue()
        self._playback_task: Optional[asyncio.Task] = None
        
        # Streaming state
        self._streaming_source: Optional[StreamingAudioSource] = None
        self._streaming_active = False
        
        # Register events
        self._setup_events()
    
    def _setup_events(self):
        """Setup Discord event handlers."""
        
        # Флаг для авто-запуска потока
        self._auto_stream_started = False

        # Audio callback for TTS streaming
        def on_audio_chunk(audio_data: np.ndarray):
            """Callback from TTS module for audio chunks."""
            # Авто-запуск потока при первом чанке
            if not self._auto_stream_started and self.voice_client and self.voice_client.is_connected():
                log("Auto-starting audio stream on first chunk",
                    role="DEBUG", stage="DISCORD_STREAM")
                self.start_audio_stream()
                self._auto_stream_started = True
            
            if self._streaming_active and self._streaming_source:
                try:
                    self._streaming_source.add_audio_chunk(audio_data)
                    log(f"Audio chunk sent to Discord: shape={audio_data.shape}",
                        role="DEBUG", stage="DISCORD_STREAM")
                except Exception as e:
                    log(f"Error sending audio chunk to Discord: {e}",
                        role="ERROR", stage="DISCORD_STREAM")
            else:
                if not self._streaming_active:
                    log(f"Audio chunk received but streaming NOT ACTIVE: source={self._streaming_source is not None}, voice_connected={self.voice_client is not None and self.voice_client.is_connected() if self.voice_client else False}",
                        role="WARN", stage="DISCORD_STREAM")
                if self._streaming_source:
                    # Поток есть, но не активен - пробуем перезапустить
                    log("Streaming source exists but not active - restarting...",
                        role="WARN", stage="DISCORD_STREAM")
                    self.start_audio_stream()

        @self.bot.event
        async def on_ready():
            log(f"Discord bot logged in as {self.bot.user}",
                role="SYSTEM", stage="DISCORD")
            self._connected = True

            # Устанавливаем callback для TTS аудио
            set_discord_audio_callback(on_audio_chunk)
            log("Discord TTS audio callback registered",
                role="DEBUG", stage="DISCORD")

            # Auto-join default channel if configured
            if self.default_guild_id and self.default_channel_id:
                await self.join_voice_channel(
                    self.default_guild_id,
                    self.default_channel_id
                )

        @self.bot.event
        async def on_voice_state_update(member, before, after):
            """Handle voice state changes."""
            if member == self.bot.user:
                if after.channel is None and self._connected:
                    log("Bot disconnected from voice channel",
                        role="DISCORD", stage="VOICE")
                    self.voice_client = None
                    self.current_channel_id = None
                    self._streaming_active = False
                    self._auto_stream_started = False

                    # Stop streaming if disconnected
                    if self._streaming_source:
                        self._streaming_source.mark_done()
                        self._streaming_source = None

                    if self.auto_reconnect and self.default_channel_id:
                        log("Auto-reconnecting to voice channel...",
                            role="DISCORD", stage="VOICE")
                        await asyncio.sleep(2)
                        await self.join_voice_channel(
                            self.default_guild_id,
                            self.default_channel_id
                        )
                elif before.channel is None and after.channel is not None:
                    # Бот вошёл в канал - сбрасываем флаг для авто-запуска
                    log("Bot joined voice channel - will auto-start stream on next audio",
                        role="DEBUG", stage="DISCORD_STREAM")
                    self._auto_stream_started = False
    
    async def connect(self):
        """
        Connect to Discord.
        
        Runs the bot in a background task.
        """
        try:
            log("Connecting to Discord...", role="SYSTEM", stage="DISCORD")
            
            # Start bot in background thread
            loop = asyncio.get_event_loop()
            self._bot_task = loop.create_task(
                self.bot.start(self.token)
            )
            
            # Wait for connection
            timeout = 30
            start_time = asyncio.get_event_loop().time()
            while not self._connected:
                await asyncio.sleep(0.1)
                if asyncio.get_event_loop().time() - start_time > timeout:
                    raise TimeoutError("Failed to connect to Discord")
            
            log("Discord connection established",
                role="SYSTEM", stage="DISCORD")
            
        except Exception as e:
            log(f"Discord connection error: {e}",
                role="ERROR", stage="DISCORD")
            raise
    
    async def disconnect(self):
        """Disconnect from Discord and cleanup."""
        try:
            log("Disconnecting from Discord...", role="SYSTEM", stage="DISCORD")
            
            # Leave voice channel
            if self.voice_client:
                await self.leave_voice_channel()
            
            # Stop bot
            if hasattr(self, '_bot_task'):
                self._bot_task.cancel()
                try:
                    await self._bot_task
                except asyncio.CancelledError:
                    pass
            
            self._connected = False
            log("Discord disconnected", role="SYSTEM", stage="DISCORD")
            
        except Exception as e:
            log(f"Discord disconnect error: {e}",
                role="ERROR", stage="DISCORD")
    
    async def join_voice_channel(
        self,
        guild_id: int,
        channel_id: int,
        timeout: float = 30.0
    ) -> bool:
        """
        Join a Discord voice channel.
        
        Args:
            guild_id: Guild (server) ID
            channel_id: Voice channel ID
            timeout: Connection timeout in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            log(f"Joining voice channel: guild={guild_id}, channel={channel_id}",
                role="DISCORD", stage="VOICE")
            
            guild = self.bot.get_guild(guild_id)
            if not guild:
                log(f"Guild {guild_id} not found",
                    role="ERROR", stage="DISCORD")
                return False
            
            channel = guild.get_channel(channel_id)
            if not channel:
                log(f"Voice channel {channel_id} not found",
                    role="ERROR", stage="DISCORD")
                return False
            
            if not isinstance(channel, discord.VoiceChannel):
                log(f"Channel {channel_id} is not a voice channel",
                    role="ERROR", stage="DISCORD")
                return False
            
            # Connect to voice channel
            self.voice_client = await channel.connect(timeout=timeout)
            self.current_guild_id = guild_id
            self.current_channel_id = channel_id
            
            # Set volume
            if hasattr(self.voice_client, 'source'):
                self.voice_client.source.volume = self.default_volume
            
            log(f"Joined voice channel: {channel.name}",
                role="DISCORD", stage="VOICE_SUCCESS")
            
            return True
            
        except Exception as e:
            log(f"Failed to join voice channel: {e}",
                role="ERROR", stage="DISCORD")
            return False
    
    async def leave_voice_channel(self) -> bool:
        """
        Leave current voice channel.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.voice_client:
                log("Leaving voice channel",
                    role="DISCORD", stage="VOICE")
                await self.voice_client.disconnect()
                self.voice_client = None
                self.current_channel_id = None
                return True
            return False
            
        except Exception as e:
            log(f"Failed to leave voice channel: {e}",
                role="ERROR", stage="DISCORD")
            return False

    def start_audio_stream(self):
        """
        Start streaming audio from TTS module.

        This enables real-time audio streaming to Discord
        from the local TTS audio output.
        """
        if not self.voice_client or not self.voice_client.is_connected():
            log("Cannot start stream: not connected to voice channel",
                role="ERROR", stage="DISCORD_STREAM")
            return False

        try:
            # Stop any current playback
            if self.voice_client.is_playing():
                log("Stopping current playback before starting stream",
                    role="DEBUG", stage="DISCORD_STREAM")
                self.voice_client.stop()

            # Create streaming source
            self._streaming_source = StreamingAudioSource(sample_rate=sample_rate)
            self._streaming_source.volume = self.default_volume

            # Start playback
            def play_callback(error):
                if error:
                    log(f"Discord playback error: {error}",
                        role="ERROR", stage="DISCORD_STREAM")
                else:
                    log("Discord playback completed",
                        role="DEBUG", stage="DISCORD_STREAM")

            self.voice_client.play(self._streaming_source, after=play_callback)
            self._streaming_active = True

            log(f"Audio stream started: volume={self.default_volume}",
                role="SYSTEM", stage="DISCORD_STREAM")

            return True

        except Exception as e:
            log(f"Failed to start audio stream: {e}",
                role="ERROR", stage="DISCORD_STREAM")
            import traceback
            log(traceback.format_exc(), role="ERROR", stage="DISCORD_STREAM")
            return False
    
    def stop_audio_stream(self):
        """
        Stop streaming audio to Discord.
        """
        try:
            if self._streaming_source:
                self._streaming_source.mark_done()
                
                # Wait for playback to finish
                if self.voice_client and self.voice_client.is_playing():
                    # Don't stop immediately, let it finish
                    pass
                
                self._streaming_source = None
                self._streaming_active = False
                
                log("Audio stream stopped",
                    role="DISCORD", stage="STREAM")
                    
        except Exception as e:
            log(f"Failed to stop audio stream: {e}",
                role="ERROR", stage="DISCORD")

    async def speak(
        self,
        text: str,
        context: Optional[ExpressionContext] = None,
        volume: Optional[float] = None,
        wait: bool = False
    ):
        """
        Speak text in voice channel using TTS.
        
        Args:
            text: Text to speak
            context: Emotional context for expressive speech
            volume: Volume override (0.0 to 2.0)
            wait: If True, wait for playback to complete
        """
        if not self.voice_client or not self.voice_client.is_connected():
            log("Not connected to voice channel, cannot speak",
                role="WARN", stage="DISCORD")
            return
        
        try:
            log(f"Speaking: {text[:50]}...",
                role="DISCORD", stage="TTS")
            
            # Create audio source
            audio_source = TTSAudioSource(
                text=text,
                use_ssml=True,
                context=context,
                sample_rate=sample_rate
            )
            
            # Set volume
            if volume is not None:
                audio_source.volume = volume
            
            # Stop current playback
            if self.voice_client.is_playing():
                self.voice_client.stop()
            
            # Play audio
            if wait:
                # Synchronous playback
                self.voice_client.play(audio_source)
                while self.voice_client.is_playing():
                    await asyncio.sleep(0.1)
            else:
                # Asynchronous playback
                self.voice_client.play(audio_source)
            
            log("TTS playback started",
                role="DISCORD", stage="TTS_DONE")
            
        except Exception as e:
            log(f"TTS speak error: {e}",
                role="ERROR", stage="DISCORD")
    
    async def speak_queue(
        self,
        text: str,
        context: Optional[ExpressionContext] = None
    ):
        """
        Add text to speech queue (sequential playback).
        
        Args:
            text: Text to speak
            context: Emotional context
        """
        await self._audio_queue.put((text, context))
        
        # Start playback if not running
        if not self._playback_task or self._playback_task.done():
            self._playback_task = asyncio.create_task(
                self._playback_loop()
            )
    
    async def _playback_loop(self):
        """Background task for queued playback."""
        while True:
            try:
                text, context = await self._audio_queue.get()
                await self.speak(text, context=context, wait=True)
            except asyncio.CancelledError:
                break
            except Exception as e:
                log(f"Playback loop error: {e}",
                    role="ERROR", stage="DISCORD")
    
    def is_connected(self) -> bool:
        """Check if connected to Discord and voice channel."""
        return (
            self._connected and
            self.voice_client is not None and
            self.voice_client.is_connected()
        )
    
    def is_playing(self) -> bool:
        """Check if currently playing audio."""
        return self.voice_client is not None and self.voice_client.is_playing()
    
    def set_volume(self, volume: float):
        """
        Set playback volume.
        
        Args:
            volume: Volume level (0.0 to 2.0)
        """
        self.default_volume = volume
        if self.voice_client and hasattr(self.voice_client, 'source'):
            self.voice_client.source.volume = volume
    
    def get_state(self) -> Dict[str, Any]:
        """Get current voice client state."""
        return {
            "connected": self._connected,
            "guild_id": self.current_guild_id,
            "channel_id": self.current_channel_id,
            "playing": self.is_playing(),
            "volume": self.default_volume,
            "queue_size": self._audio_queue.qsize()
        }


# Convenience functions for quick integration

_voice_client: Optional[DiscordVoiceClient] = None


def get_voice_client() -> Optional[DiscordVoiceClient]:
    """Get global voice client instance."""
    return _voice_client


async def init_discord_voice(
    token: str,
    guild_id: int,
    channel_id: int,
    volume: float = 1.0
) -> DiscordVoiceClient:
    """
    Initialize and connect Discord voice client.
    
    Args:
        token: Discord bot token
        guild_id: Guild ID
        channel_id: Voice channel ID
        volume: Default volume
        
    Returns:
        Connected DiscordVoiceClient instance
    """
    global _voice_client
    
    _voice_client = DiscordVoiceClient(
        token=token,
        guild_id=guild_id,
        channel_id=channel_id,
        volume=volume
    )
    
    await _voice_client.connect()
    return _voice_client


async def shutdown_discord_voice():
    """Shutdown Discord voice client."""
    global _voice_client
    
    if _voice_client:
        await _voice_client.disconnect()
        _voice_client = None

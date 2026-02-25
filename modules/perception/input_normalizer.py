"""
Perception Layer - Handles input normalization and initial signal processing.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass
class PerceivedInput:
    """Normalized perception output."""
    text: str
    speaker: str = "user"
    timestamp: datetime = field(default_factory=datetime.now)
    context_signals: Dict[str, Any] = field(default_factory=dict)
    
    # Raw signals
    voice_features: Optional[Dict[str, float]] = None
    silence_duration: float = 0.0
    interruption: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "speaker": self.speaker,
            "timestamp": self.timestamp.isoformat(),
            "context_signals": self.context_signals,
            "voice_features": self.voice_features,
            "silence_duration": self.silence_duration,
            "interruption": self.interruption
        }


class InputNormalizer:
    """
    Normalizes raw input from STT and other sensors.
    """
    
    def __init__(self):
        self._default_speaker = "user"
    
    def normalize(
        self,
        text: str,
        speaker: Optional[str] = None,
        voice_features: Optional[Dict[str, float]] = None,
        silence_duration: float = 0.0,
        interruption: bool = False,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> PerceivedInput:
        """
        Normalize raw input into structured PerceivedInput.
        
        Args:
            text: Raw text from STT
            speaker: Speaker identifier
            voice_features: Voice characteristics (pitch, energy, etc.)
            silence_duration: Duration of silence before this input
            interruption: Whether this interrupted the assistant
            additional_context: Additional context signals
            
        Returns:
            Normalized PerceivedInput
        """
        # Clean and normalize text
        cleaned_text = self._clean_text(text)
        
        # Build context signals
        context_signals = self._build_context_signals(
            voice_features=voice_features,
            silence_duration=silence_duration,
            interruption=interruption,
            additional=additional_context
        )
        
        return PerceivedInput(
            text=cleaned_text,
            speaker=speaker or self._default_speaker,
            timestamp=datetime.now(),
            context_signals=context_signals,
            voice_features=voice_features,
            silence_duration=silence_duration,
            interruption=interruption
        )
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = " ".join(text.split())
        
        # Remove common speech artifacts
        artifacts = ["ммм", "эээ", "ну", "как бы", "типа"]
        for artifact in artifacts:
            text = text.replace(artifact, "")
        
        return text.strip()
    
    def _build_context_signals(
        self,
        voice_features: Optional[Dict[str, float]],
        silence_duration: float,
        interruption: bool,
        additional: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build context signals from various inputs."""
        signals = {
            "silence_duration": silence_duration,
            "interruption": interruption,
            "has_voice_features": voice_features is not None
        }
        
        if voice_features:
            signals["voice"] = voice_features
        
        if additional:
            signals.update(additional)
        
        return signals

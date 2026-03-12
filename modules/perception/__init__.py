"""
Perception Layer - Main module.
"""

from modules.perception.input_normalizer import InputNormalizer, PerceivedInput
from modules.perception.emotion_detector import EmotionDetector, EmotionState
from modules.perception.intent_detector import IntentDetector, IntentResult

__all__ = [
    "InputNormalizer",
    "PerceivedInput",
    "EmotionDetector",
    "EmotionState",
    "IntentDetector",
    "IntentResult"
]


class PerceptionLayer:
    """
    Unified Perception Layer that combines all perception modules.
    
    Input: Raw text and signals from STT
    Output: Structured perception data for Interpretation Layer
    """
    
    def __init__(self):
        self.normalizer = InputNormalizer()
        self.emotion_detector = EmotionDetector()
        self.intent_detector = IntentDetector()
    
    def process(
        self,
        text: str,
        speaker: str = "user",
        voice_features: dict = None,
        silence_duration: float = 0.0,
        interruption: bool = False,
        additional_context: dict = None
    ) -> dict:
        """
        Process raw input through all perception modules.
        
        Args:
            text: Raw text from STT
            speaker: Speaker identifier
            voice_features: Voice characteristics from audio
            silence_duration: Duration of silence before input
            interruption: Whether this interrupted the assistant
            additional_context: Additional context signals
            
        Returns:
            Structured perception output
        """
        # Step 1: Normalize input
        perceived = self.normalizer.normalize(
            text=text,
            speaker=speaker,
            voice_features=voice_features,
            silence_duration=silence_duration,
            interruption=interruption,
            additional_context=additional_context
        )
        
        # Step 2: Detect emotion
        emotion = self.emotion_detector.detect(
            text=perceived.text,
            voice_features=voice_features
        )
        
        # Step 3: Detect intent
        intent = self.intent_detector.detect(perceived.text)
        
        # Combine results
        return {
            "perceived_input": perceived.to_dict(),
            "emotion": emotion.to_dict(),
            "intent": intent.to_dict()
        }

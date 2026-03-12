"""
TTS Expression Processor - Converts text with emotional context into SSML for expressive speech.

This module analyzes LLM response metadata (emotion, tone, decision strategy) and
generates SSML-enhanced text with prosody markers for Silero TTS.
"""

import re
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass


@dataclass
class ExpressionContext:
    """Context for expression processing."""
    emotion: Optional[Dict[str, float]] = None
    emotional_tone: str = "NEUTRAL"
    decision_strategy: str = "ANSWER_DIRECT"
    dominant_trait: str = "neutral"
    engagement_level: float = 0.5
    user_emotion: Optional[Dict[str, float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "emotion": self.emotion,
            "emotional_tone": self.emotional_tone,
            "decision_strategy": self.decision_strategy,
            "dominant_trait": self.dominant_trait,
            "engagement_level": self.engagement_level,
            "user_emotion": self.user_emotion
        }


class TTSExpressionProcessor:
    """
    Processes text with emotional context to generate SSML for expressive TTS.
    
    SSML features used:
    - <prosody rate/pitch/volume> - for emotional expression
    - <break time="..."/> - for dramatic pauses
    - <s> - for sentence-level control
    - <p> - for paragraph breaks
    """
    
    # Emotion to prosody mapping
    EMOTION_PROSODY = {
        # Basic emotions (Ekman)
        "joy": {
            "rate": "medium", "pitch": "high", "volume": "loud",
            "break_before": "100ms", "break_after": "200ms"
        },
        "sadness": {
            "rate": "slow", "pitch": "low", "volume": "soft",
            "break_before": "300ms", "break_after": "400ms"
        },
        "anger": {
            "rate": "fast", "pitch": "low", "volume": "loud",
            "break_before": "50ms", "break_after": "100ms"
        },
        "fear": {
            "rate": "fast", "pitch": "high", "volume": "soft",
            "break_before": "200ms", "break_after": "150ms"
        },
        "surprise": {
            "rate": "medium", "pitch": "x-high", "volume": "medium",
            "break_before": "400ms", "break_after": "300ms"
        },
        "disgust": {
            "rate": "slow", "pitch": "low", "volume": "medium",
            "break_before": "200ms", "break_after": "250ms"
        },
        # Complex emotions
        "excitement": {
            "rate": "fast", "pitch": "high", "volume": "loud",
            "break_before": "50ms", "break_after": "100ms"
        },
        "calm": {
            "rate": "slow", "pitch": "medium", "volume": "soft",
            "break_before": "300ms", "break_after": "300ms"
        },
        "curiosity": {
            "rate": "medium", "pitch": "high", "volume": "medium",
            "break_before": "200ms", "break_after": "200ms"
        },
        "empathy": {
            "rate": "slow", "pitch": "medium", "volume": "soft",
            "break_before": "400ms", "break_after": "400ms"
        },
        "neutral": {
            "rate": "medium", "pitch": "medium", "volume": "medium",
            "break_before": "100ms", "break_after": "100ms"
        }
    }
    
    # Decision strategy to speech style
    STRATEGY_STYLE = {
        "ANSWER_DIRECT": {"rate": "medium", "pitch": "medium"},
        "EXPLAIN": {"rate": "slow", "pitch": "medium"},
        "EXPLORE": {"rate": "medium", "pitch": "high"},
        "SUPPORT": {"rate": "slow", "pitch": "medium"},
        "ENGAGE": {"rate": "fast", "pitch": "high"},
        "REFLECT": {"rate": "x-slow", "pitch": "low"},
        "CREATIVE": {"rate": "medium", "pitch": "high"},
        "ANALYTICAL": {"rate": "medium", "pitch": "low"}
    }
    
    # Trait-specific speech patterns
    TRAIT_SPEECH = {
        "curiosity": {"rate": "medium", "pitch": "high", "pause_extra": "100ms"},
        "empathy": {"rate": "slow", "pitch": "medium", "pause_extra": "200ms"},
        "humor": {"rate": "fast", "pitch": "high", "pause_extra": "50ms"},
        "conscientiousness": {"rate": "slow", "pitch": "low", "pause_extra": "150ms"},
        "creativity": {"rate": "medium", "pitch": "high", "pause_extra": "100ms"},
        "extraversion": {"rate": "fast", "pitch": "high", "pause_extra": "50ms"},
        "openness": {"rate": "medium", "pitch": "high", "pause_extra": "100ms"},
        "neuroticism": {"rate": "fast", "pitch": "high", "pause_extra": "200ms"}
    }
    
    # Punctuation-based pause mapping
    PUNCTUATION_PAUSE = {
        ".": "300ms",
        "!": "400ms",
        "?": "350ms",
        ",": "150ms",
        ";": "200ms",
        ":": "200ms",
        "...": "600ms",
        "—": "250ms",
        "-": "200ms"
    }
    
    def process(
        self,
        text: str,
        context: Optional[ExpressionContext] = None
    ) -> str:
        """
        Process text with emotional context into SSML.
        
        Args:
            text: Input text to convert to SSML
            context: Emotional and decision context
            
        Returns:
            SSML-enhanced text for expressive TTS
        """
        if context is None:
            context = ExpressionContext()
        
        # Determine primary emotion
        primary_emotion = self._get_primary_emotion(context.emotion)
        
        # Get prosody settings
        emotion_prosody = self.EMOTION_PROSODY.get(primary_emotion, self.EMOTION_PROSODY["neutral"])
        strategy_style = self.STRATEGY_STYLE.get(context.decision_strategy, self.STRATEGY_STYLE["ANSWER_DIRECT"])
        trait_speech = self.TRAIT_SPEECH.get(context.dominant_trait, self.TRAIT_SPEECH["curiosity"])
        
        # Merge settings (emotion takes priority)
        prosody_settings = {
            "rate": strategy_style.get("rate", emotion_prosody["rate"]),
            "pitch": emotion_prosody["pitch"],
            "volume": emotion_prosody["volume"]
        }
        
        # Apply trait modifications
        if context.dominant_trait in self.TRAIT_SPEECH:
            if context.engagement_level > 0.7:
                prosody_settings["rate"] = "fast"
            elif context.engagement_level < 0.3:
                prosody_settings["rate"] = "slow"
        
        # Split into sentences
        sentences = self._split_sentences(text)
        
        # Build SSML
        ssml_parts = ['<speak>']
        ssml_parts.append('<p>')
        
        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Process individual sentence
            processed_sentence = self._process_sentence(
                sentence,
                prosody_settings,
                emotion_prosody,
                is_first=i == 0,
                is_last=i == len(sentences) - 1
            )
            ssml_parts.append(processed_sentence)
            
            # Add break after sentence if needed
            if not is_last_sentence(sentence):
                break_time = emotion_prosody.get("break_after", "100ms")
                ssml_parts.append(f'<break time="{break_time}"/>')
        
        ssml_parts.append('</p>')
        ssml_parts.append('</speak>')
        
        return '\n'.join(ssml_parts)
    
    def _get_primary_emotion(self, emotion: Optional[Dict[str, float]]) -> str:
        """Extract primary emotion from emotion dictionary."""
        if not emotion:
            return "neutral"
        
        # Find emotion with highest value
        max_emotion = max(emotion.items(), key=lambda x: x[1], default=("neutral", 0))
        
        if max_emotion[1] < 0.3:  # Threshold for significant emotion
            return "neutral"
        
        return max_emotion[0].lower()
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Handle common sentence boundaries
        sentences = re.split(r'(?<=[.!?…])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _process_sentence(
        self,
        sentence: str,
        prosody_settings: Dict[str, str],
        emotion_prosody: Dict[str, str],
        is_first: bool = False,
        is_last: bool = False
    ) -> str:
        """Process individual sentence with prosody markers."""
        rate = prosody_settings["rate"]
        pitch = prosody_settings["pitch"]
        volume = prosody_settings["volume"]
        
        # Add break before if not first sentence
        break_before = ""
        if not is_first and "break_before" in emotion_prosody:
            break_before = f'<break time="{emotion_prosody["break_before"]}"/>'
        
        # Check for emotional keywords that need emphasis
        emphasized = self._add_emphasis(sentence, pitch)
        
        # Wrap in prosody tags
        prosody_open = f'<prosody rate="{rate}" pitch="{pitch}" volume="{volume}">'
        prosody_close = '</prosody>'
        
        return f'{break_before}<s>{prosody_open}{emphasized}{prosody_close}</s>'
    
    def _add_emphasis(self, sentence: str, pitch: str) -> str:
        """Add emphasis to emotionally significant words."""
        # Emphasis patterns (Russian)
        emphasis_words = {
            "очень": True,
            "крайне": True,
            "невероятно": True,
            "действительно": True,
            "действительно": True,
            "правда": True,
            "точно": True,
            "именно": True,
            "особенно": True,
            "главное": True,
            "важно": True,
            "понимаю": True,
            "чувствую": True,
            "знаю": True,
            "думаю": True,
            "считаю": True
        }
        
        words = sentence.split()
        emphasized_words = []
        
        for word in words:
            clean_word = re.sub(r'[^\wа-яё]', '', word.lower())
            if clean_word in emphasis_words:
                # Add emphasis using pitch change
                emphasized_words.append(f'<prosody pitch="x-{pitch}">{word}</prosody>')
            else:
                emphasized_words.append(word)
        
        return ' '.join(emphasized_words)
    
    def process_with_user_emotion(
        self,
        text: str,
        context: ExpressionContext,
        user_text: str
    ) -> str:
        """
        Process text considering both assistant emotion and user emotion.
        
        Args:
            text: Assistant response text
            context: Expression context
            user_text: Original user input for additional context
            
        Returns:
            SSML-enhanced text
        """
        # Adjust based on user emotion
        if context.user_emotion:
            user_primary = self._get_primary_emotion(context.user_emotion)
            
            # If user is sad, be more empathetic
            if user_primary == "sadness":
                context.dominant_trait = "empathy"
                context.emotional_tone = "EMPATHETIC"
            
            # If user is angry, be calmer
            elif user_primary == "anger":
                context.emotional_tone = "CALM"
                context.decision_strategy = "SUPPORT"
            
            # If user is excited, match energy
            elif user_primary == "joy":
                context.engagement_level = 0.8
        
        return self.process(text, context)


def is_last_sentence(sentence: str) -> bool:
    """
    Check if sentence is likely the last one.
    
    Checks for terminal punctuation that typically ends a statement.
    """
    if not sentence:
        return False
    
    # Strip trailing whitespace and quotes
    cleaned = sentence.strip().rstrip('"\'"')
    
    if not cleaned:
        return False
    
    # Terminal punctuation marks
    terminal_punctuation = {'.', '!', '?', '…', '...'}
    
    # Check if sentence ends with terminal punctuation
    return cleaned[-1] in terminal_punctuation


def validate_ssml(ssml_text: str) -> Tuple[bool, Optional[str]]:
    """
    Validate SSML text for well-formed XML and required elements.
    
    Args:
        ssml_text: SSML string to validate
        
    Returns:
        Tuple of (is_valid, error_message)
        If valid, error_message is None
    """
    if not ssml_text:
        return False, "Empty SSML text"
    
    # Check for required speak tag
    if '<speak' not in ssml_text or '</speak>' not in ssml_text:
        return False, "Missing <speak> root element"
    
    try:
        # Try to parse as XML
        ET.fromstring(ssml_text)
        return True, None
    except ET.ParseError as e:
        return False, f"XML parse error: {str(e)}"


def repair_ssml(ssml_text: str) -> str:
    """
    Attempt to repair common SSML errors.
    
    Args:
        ssml_text: SSML string to repair
        
    Returns:
        Repaired SSML string
    """
    if not ssml_text:
        return ssml_text
    
    # Ensure speak root element exists
    if '<speak' not in ssml_text:
        ssml_text = '<speak>' + ssml_text + '</speak>'
    
    # Fix unclosed tags (basic repair)
    # Count opening and closing tags
    for tag in ['prosody', 's', 'p', 'break']:
        open_count = ssml_text.count(f'<{tag}')
        close_count = ssml_text.count(f'</{tag}>')
        
        # Self-closing break tags
        if tag == 'break':
            # Ensure break tags are self-closing
            ssml_text = re.sub(r'<break([^>]*)>(?!</break>)', r'<break\1/>', ssml_text)
        else:
            # Close unclosed tags
            if open_count > close_count:
                ssml_text += f'</{tag}>' * (open_count - close_count)
    
    return ssml_text


def strip_ssml(ssml_text: str) -> str:
    """
    Strip SSML tags and return plain text.
    
    Args:
        ssml_text: SSML string
        
    Returns:
        Plain text without SSML tags
    """
    if not ssml_text:
        return ssml_text
    
    # Remove all XML/SSML tags
    plain_text = re.sub(r'<[^>]+>', '', ssml_text)
    
    # Clean up extra whitespace
    plain_text = re.sub(r'\s+', ' ', plain_text).strip()
    
    return plain_text


# Convenience function for direct use
def convert_to_ssml(
    text: str,
    emotion: Optional[Dict[str, float]] = None,
    emotional_tone: str = "NEUTRAL",
    decision_strategy: str = "ANSWER_DIRECT",
    dominant_trait: str = "neutral",
    engagement_level: float = 0.5,
    user_emotion: Optional[Dict[str, float]] = None,
    validate: bool = True,
    repair: bool = True
) -> str:
    """
    Convert text to SSML with emotional expression.

    Args:
        text: Input text
        emotion: Emotion dictionary (e.g., {"joy": 0.8, "surprise": 0.3})
        emotional_tone: Emotional tone from decision layer
        decision_strategy: Response strategy
        dominant_trait: Dominant personality trait
        engagement_level: User engagement level (0-1)
        user_emotion: User's emotion from their message
        validate: Whether to validate SSML after generation
        repair: Whether to attempt repair of invalid SSML

    Returns:
        SSML string for expressive TTS
    """
    processor = TTSExpressionProcessor()
    context = ExpressionContext(
        emotion=emotion,
        emotional_tone=emotional_tone,
        decision_strategy=decision_strategy,
        dominant_trait=dominant_trait,
        engagement_level=engagement_level,
        user_emotion=user_emotion
    )

    if user_emotion:
        ssml = processor.process_with_user_emotion(text, context, user_text="")
    else:
        ssml = processor.process(text, context)

    # Validate and optionally repair
    if validate:
        is_valid, error = validate_ssml(ssml)
        if not is_valid:
            from modules.stt.logger import log
            log(f"SSML validation failed: {error}", role="WARN", stage="TTS")
            
            if repair:
                log("Attempting SSML repair...", role="DEBUG", stage="TTS")
                ssml = repair_ssml(ssml)
                
                # Re-validate after repair
                is_valid, error = validate_ssml(ssml)
                if not is_valid:
                    log(f"Repair failed, falling back to plain text: {error}", 
                        role="WARN", stage="TTS")
                    return text  # Fallback to plain text
                else:
                    log("SSML repair successful", role="DEBUG", stage="TTS")
            else:
                log(f"SSML invalid and repair disabled, using plain text: {error}", 
                    role="WARN", stage="TTS")
                return text  # Fallback to plain text

    return ssml

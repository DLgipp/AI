"""
Emotion Detection Module - Detects emotional state from text and voice.
"""

from dataclasses import dataclass
from typing import Dict, Optional, List
import re


@dataclass
class EmotionState:
    """Detected emotional state."""
    valence: float = 0.0  # -1.0 (negative) to +1.0 (positive)
    arousal: float = 0.0  # 0.0 (calm) to 1.0 (excited)
    dominance: float = 0.5  # 0.0 (submissive) to 1.0 (dominant)
    
    # Discrete emotions (confidence scores 0-1)
    joy: float = 0.0
    sadness: float = 0.0
    anger: float = 0.0
    fear: float = 0.0
    surprise: float = 0.0
    disgust: float = 0.0
    neutral: float = 1.0
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "valence": self.valence,
            "arousal": self.arousal,
            "dominance": self.dominance,
            "joy": self.joy,
            "sadness": self.sadness,
            "anger": self.anger,
            "fear": self.fear,
            "surprise": self.surprise,
            "disgust": self.disgust,
            "neutral": self.neutral
        }
    
    @property
    def dominant_emotion(self) -> str:
        """Get the most prominent emotion."""
        emotions = {
            "joy": self.joy,
            "sadness": self.sadness,
            "anger": self.anger,
            "fear": self.fear,
            "surprise": self.surprise,
            "disgust": self.disgust,
            "neutral": self.neutral
        }
        return max(emotions, key=emotions.get)


class EmotionDetector:
    """
    Rule-based emotion detector (can be extended with ML models).
    """
    
    # Russian emotion lexicon (simplified)
    POSITIVE_WORDS = {
        "хорошо", "отлично", "прекрасно", "замечательно", "рад", "рада",
        "счастлив", "счастлива", "весело", "круто", "класс", "восхищаюсь",
        "люблю", "нравится", "удивительно", "восхитительно", "смешно",
        "ха-ха", "ахаха", "лол", "здорово", "приятно", "благодарю", "спасибо"
    }
    
    NEGATIVE_WORDS = {
        "плохо", "ужасно", "страшно", "грустно", "печально", "тоскливо",
        "злюсь", "зол", "зла", "раздражает", "бесит", "отвратительно",
        "ненавижу", "кошмар", "устал", "устала", "скучно", "тоска",
        "больно", "обидно", "жаль", "сожалею", "разочарован", "разочарована"
    }
    
    ANGER_WORDS = {
        "злюсь", "зол", "зла", "бесит", "раздражает", "ненавижу",
        "какой ужас", "это отвратительно", "прекрати", "отстань"
    }
    
    FEAR_WORDS = {
        "боюсь", "страшно", "пугает", "тревожно", "беспокоюсь",
        "переживаю", "волнуюсь", "опасно", "ужас"
    }
    
    SADNESS_WORDS = {
        "грустно", "печально", "тоскливо", "жаль", "плачу", "рыдаю",
        "депрессия", "устал", "устала", "нет сил", "опустились руки"
    }
    
    SURPRISE_WORDS = {
        "вау", "ого", "ничего себе", "неожиданно", "удивлен", "удивлена",
        "поразительно", "не верю", "правда?", "серьезно?", "что?!"
    }
    
    # Intensity markers
    INTENSIFIERS = {
        "очень": 1.5,
        "крайне": 1.8,
        "ужасно": 1.7,
        "невероятно": 1.6,
        "слишком": 1.4,
        "чрезвычайно": 1.7,
        "весьма": 1.3,
        "действительно": 1.3
    }
    
    # Negation reduces intensity
    NEGATIONS = {"не", "нет", "ни", "никак", "нисколько"}
    
    def detect(self, text: str, voice_features: Optional[Dict[str, float]] = None) -> EmotionState:
        """
        Detect emotion from text and optional voice features.
        
        Args:
            text: Input text
            voice_features: Optional voice characteristics
            
        Returns:
            EmotionState with detected emotions
        """
        text_lower = text.lower()
        words = set(re.findall(r'\w+', text_lower))
        
        # Initialize emotion scores
        emotion = EmotionState()
        
        # Detect discrete emotions
        emotion.joy = self._detect_emotion_category(words, self.POSITIVE_WORDS)
        emotion.sadness = self._detect_emotion_category(words, self.SADNESS_WORDS)
        emotion.anger = self._detect_emotion_category(words, self.ANGER_WORDS)
        emotion.fear = self._detect_emotion_category(words, self.FEAR_WORDS)
        emotion.surprise = self._detect_emotion_category(words, self.SURPRISE_WORDS)
        
        # Calculate valence from positive/negative balance
        positive_score = self._count_matches(words, self.POSITIVE_WORDS)
        negative_score = self._count_matches(words, self.NEGATIVE_WORDS)
        
        # Apply intensifiers
        intensifier_mult = self._detect_intensifiers(words)
        positive_score *= intensifier_mult
        negative_score *= intensifier_mult
        
        # Apply negations (simplified)
        if self._has_negation(words):
            positive_score, negative_score = negative_score * 0.5, positive_score * 0.5
        
        # Normalize valence (-1 to +1)
        total = positive_score + negative_score + 0.1  # avoid division by zero
        emotion.valence = (positive_score - negative_score) / total
        emotion.valence = max(-1.0, min(1.0, emotion.valence))
        
        # Calculate arousal from intensity and voice
        emotion.arousal = self._calculate_arousal(text, voice_features)
        
        # Calculate dominance (simplified - based on text patterns)
        emotion.dominance = self._calculate_dominance(text)
        
        # Set neutral as inverse of total emotion
        total_emotion = (
            emotion.joy + emotion.sadness + emotion.anger +
            emotion.fear + emotion.surprise + emotion.disgust
        )
        emotion.neutral = max(0.0, 1.0 - total_emotion)
        
        # Normalize discrete emotions to sum to 1
        if total_emotion > 0:
            scale = 0.9 / total_emotion  # leave 0.1 for neutral minimum
            emotion.joy = min(1.0, emotion.joy * scale)
            emotion.sadness = min(1.0, emotion.sadness * scale)
            emotion.anger = min(1.0, emotion.anger * scale)
            emotion.fear = min(1.0, emotion.fear * scale)
            emotion.surprise = min(1.0, emotion.surprise * scale)
            emotion.disgust = min(1.0, emotion.disgust * scale)
            emotion.neutral = 0.1
        
        return emotion
    
    def _detect_emotion_category(self, words: set, lexicon: set) -> float:
        """Detect presence of emotion category."""
        matches = len(words & lexicon)
        if matches == 0:
            return 0.0
        elif matches == 1:
            return 0.3
        elif matches == 2:
            return 0.6
        else:
            return min(1.0, 0.6 + (matches - 2) * 0.15)
    
    def _count_matches(self, words: set, lexicon: set) -> float:
        """Count matching words."""
        return len(words & lexicon)
    
    def _detect_intensifiers(self, words: set) -> float:
        """Detect intensifier words and return multiplier."""
        intensifier_matches = words & set(self.INTENSIFIERS.keys())
        if not intensifier_matches:
            return 1.0
        
        max_mult = 1.0
        for word in intensifier_matches:
            mult = self.INTENSIFIERS[word]
            max_mult = max(max_mult, mult)
        
        return max_mult
    
    def _has_negation(self, words: set) -> bool:
        """Check for negation words."""
        return bool(words & self.NEGATIONS)
    
    def _calculate_arousal(
        self,
        text: str,
        voice_features: Optional[Dict[str, float]]
    ) -> float:
        """Calculate arousal level."""
        arousal = 0.5  # baseline
        
        # Text-based arousal
        if text.endswith("!"):
            arousal += 0.2
        if text.isupper():
            arousal += 0.2
        if len(text) > 100:
            arousal += 0.1  # longer messages may indicate excitement
        
        # Voice-based arousal
        if voice_features:
            # Higher energy/pitch variance = higher arousal
            energy = voice_features.get("energy", 0.5)
            pitch_variance = voice_features.get("pitch_variance", 0.5)
            arousal = (arousal + energy + pitch_variance) / 3
        
        return max(0.0, min(1.0, arousal))
    
    def _calculate_dominance(self, text: str) -> float:
        """Calculate dominance level from text patterns."""
        dominance = 0.5  # baseline
        
        text_lower = text.lower()
        
        # Commands and imperatives increase dominance
        command_patterns = ["сделай", "дай", "покажи", "расскажи", "объясни"]
        for pattern in command_patterns:
            if pattern in text_lower:
                dominance += 0.1
        
        # Questions may indicate lower dominance
        if "?" in text:
            dominance -= 0.1
        
        # Polite forms may indicate lower dominance
        polite_words = ["пожалуйста", "будьте добры", "можно", "не могли бы"]
        for word in polite_words:
            if word in text_lower:
                dominance -= 0.1
        
        return max(0.0, min(1.0, dominance))

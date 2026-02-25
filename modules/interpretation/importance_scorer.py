"""
Importance Scorer Module - Calculates importance of input.
"""

from dataclasses import dataclass
from typing import Dict, Optional, Any


@dataclass
class ImportanceResult:
    """Importance scoring result."""
    importance: float = 0.5  # 0.0 (low) to 1.0 (high)
    factors: Dict[str, float] = None
    reasoning: str = ""
    
    def __post_init__(self):
        if self.factors is None:
            self.factors = {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "importance": self.importance,
            "factors": self.factors,
            "reasoning": self.reasoning
        }


class ImportanceScorer:
    """
    Calculates importance score based on multiple factors.
    """
    
    # Weights for different factors
    WEIGHTS = {
        "emotion_intensity": 0.20,
        "urgency": 0.20,
        "goal_priority": 0.20,
        "topic_relevance": 0.15,
        "user_engagement": 0.15,
        "context_importance": 0.10
    }
    
    # Important topics (higher relevance)
    IMPORTANT_TOPICS = {
        "health": 0.9,
        "safety": 0.95,
        "mental_health": 0.85,
        "relationships": 0.7,
        "work": 0.6,
        "education": 0.65,
        "finance": 0.7
    }
    
    # Low importance topics
    LOW_IMPORTANCE_TOPICS = {
        "humor": 0.3,
        "entertainment": 0.4,
        "gossip": 0.2,
        "small_talk": 0.3
    }
    
    def calculate(
        self,
        text: str,
        emotion: Optional[Dict[str, float]] = None,
        goal: Optional[Dict[str, Any]] = None,
        topic: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        silence_duration: float = 0.0
    ) -> ImportanceResult:
        """
        Calculate importance score.
        
        Args:
            text: Input text
            emotion: Detected emotion
            goal: Extracted goal
            topic: Detected topic
            context: Conversation context
            silence_duration: Duration of silence before input
            
        Returns:
            ImportanceResult with score and factors
        """
        factors = {}
        reasoning_parts = []
        
        # Factor 1: Emotion intensity
        emotion_score = self._calculate_emotion_factor(emotion)
        factors["emotion_intensity"] = emotion_score
        if emotion_score > 0.7:
            reasoning_parts.append("high emotional intensity")
        
        # Factor 2: Urgency (from goal)
        urgency_score = self._calculate_urgency_factor(goal)
        factors["urgency"] = urgency_score
        if urgency_score > 0.7:
            reasoning_parts.append("high urgency")
        
        # Factor 3: Goal priority
        priority_score = self._calculate_priority_factor(goal)
        factors["goal_priority"] = priority_score
        if priority_score > 0.7:
            reasoning_parts.append("high priority goal")
        
        # Factor 4: Topic relevance
        topic_score = self._calculate_topic_factor(topic)
        factors["topic_relevance"] = topic_score
        if topic_score > 0.7:
            reasoning_parts.append("important topic")
        
        # Factor 5: User engagement
        engagement_score = self._calculate_engagement_factor(text, silence_duration)
        factors["user_engagement"] = engagement_score
        if engagement_score > 0.7:
            reasoning_parts.append("high engagement")
        
        # Factor 6: Context importance
        context_score = self._calculate_context_factor(context)
        factors["context_importance"] = context_score
        if context_score > 0.7:
            reasoning_parts.append("important context")
        
        # Calculate weighted score
        importance = sum(
            factors.get(factor, 0.5) * weight
            for factor, weight in self.WEIGHTS.items()
        )
        
        # Normalize to 0-1
        importance = max(0.0, min(1.0, importance))
        
        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "standard importance"
        
        return ImportanceResult(
            importance=importance,
            factors=factors,
            reasoning=reasoning
        )
    
    def _calculate_emotion_factor(self, emotion: Optional[Dict[str, float]]) -> float:
        """Calculate emotion intensity factor."""
        if not emotion:
            return 0.5
        
        # High intensity emotions increase importance
        high_intensity = max(
            emotion.get("anger", 0),
            emotion.get("fear", 0),
            emotion.get("sadness", 0),
            emotion.get("joy", 0)
        )
        
        # Arousal level
        arousal = emotion.get("arousal", 0.5)
        
        # Combined score
        return (high_intensity + arousal) / 2
    
    def _calculate_urgency_factor(self, goal: Optional[Dict[str, Any]]) -> float:
        """Calculate urgency factor from goal."""
        if not goal:
            return 0.5
        
        return goal.get("urgency", 0.5)
    
    def _calculate_priority_factor(self, goal: Optional[Dict[str, Any]]) -> float:
        """Calculate priority factor from goal."""
        if not goal:
            return 0.5
        
        return goal.get("priority", 0.5)
    
    def _calculate_topic_factor(self, topic: Optional[Dict[str, Any]]) -> float:
        """Calculate topic relevance factor."""
        if not topic:
            return 0.5
        
        topic_name = topic.get("primary_topic", "general")
        category = topic.get("category", "general")
        
        # Check important topics
        for imp_topic, score in self.IMPORTANT_TOPICS.items():
            if imp_topic in topic_name.lower() or imp_topic in category.lower():
                return score
        
        # Check low importance topics
        for low_topic, score in self.LOW_IMPORTANCE_TOPICS.items():
            if low_topic in topic_name.lower() or low_topic in category.lower():
                return score
        
        return 0.5  # neutral
    
    def _calculate_engagement_factor(
        self,
        text: str,
        silence_duration: float
    ) -> float:
        """Calculate user engagement factor."""
        engagement = 0.5
        
        # Text length (longer = more engaged, to a point)
        text_len = len(text)
        if 20 <= text_len <= 200:
            engagement += 0.2
        elif text_len > 200:
            engagement += 0.1
        
        # Questions indicate engagement
        if "?" in text:
            engagement += 0.15
        
        # Personal pronouns indicate engagement
        personal_words = ["я", "мы", "мне", "нам", "свой", "своё"]
        if any(word in text.lower() for word in personal_words):
            engagement += 0.1
        
        # Long silence may indicate disengagement or deep thought
        if silence_duration > 60:
            engagement -= 0.1
        elif silence_duration > 300:
            engagement -= 0.2
        
        return max(0.0, min(1.0, engagement))
    
    def _calculate_context_factor(self, context: Optional[Dict[str, Any]]) -> float:
        """Calculate context importance factor."""
        if not context:
            return 0.5
        
        importance = 0.5
        
        # Check for ongoing task
        if context.get("ongoing_task"):
            importance += 0.2
        
        # Check for active goal
        if context.get("active_goal"):
            importance += 0.15
        
        # Check for recent important event
        if context.get("recent_important_event"):
            importance += 0.25
        
        # Check conversation depth
        conversation_turns = context.get("conversation_turns", 0)
        if 3 <= conversation_turns <= 10:
            importance += 0.1  # Active conversation
        
        return max(0.0, min(1.0, importance))

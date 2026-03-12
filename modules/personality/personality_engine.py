"""
Personality Engine - Calculates stance, value alignment, and cognitive conflicts.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from modules.memory.personality_memory import PersonalityState


@dataclass
class PersonalityStance:
    """
    Personality's stance toward a specific situation.
    Used by Decision Layer and Prompt Builder.
    """
    # Attitude toward the topic (-1.0 to +1.0)
    topic_valence: float = 0.0
    
    # Confidence in position (0.0 to 1.0)
    confidence: float = 0.5
    
    # Engagement level (0.0 to 1.0)
    engagement_level: float = 0.5
    
    # Dominant trait influencing this stance
    dominant_trait: str = "neutral"
    
    # Emotional state
    emotion_tone: float = 0.0  # -1.0 (negative) to +1.0 (positive)
    
    # Relationship with user
    user_relationship: float = 0.5  # 0.0 (distant) to 1.0 (close)
    
    # Value alignment scores
    value_alignment: Dict[str, float] = field(default_factory=dict)
    
    # Cognitive conflicts (internal tensions)
    cognitive_conflicts: List[Dict[str, Any]] = field(default_factory=list)
    
    # Behavioral tendencies
    verbosity: float = 0.5  # 0.0 (brief) to 1.0 (detailed)
    initiative: float = 0.5  # 0.0 (reactive) to 1.0 (proactive)
    formality: float = 0.5  # 0.0 (casual) to 1.0 (formal)
    emotional_expression: float = 0.5  # 0.0 (reserved) to 1.0 (expressive)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic_valence": self.topic_valence,
            "confidence": self.confidence,
            "engagement_level": self.engagement_level,
            "dominant_trait": self.dominant_trait,
            "emotion_tone": self.emotion_tone,
            "user_relationship": self.user_relationship,
            "value_alignment": self.value_alignment,
            "cognitive_conflicts": self.cognitive_conflicts,
            "verbosity": self.verbosity,
            "initiative": self.initiative,
            "formality": self.formality,
            "emotional_expression": self.emotional_expression
        }


class PersonalityEngine:
    """
    Engine for calculating personality stance and managing personality dynamics.
    """
    
    # Trait influence on behavior parameters
    TRAIT_INFLUENCES = {
        "openness": {
            "initiative": 0.3,
            "verbosity": 0.2,
            "emotional_expression": 0.1
        },
        "conscientiousness": {
            "formality": 0.3,
            "verbosity": 0.2,
            "confidence": 0.2
        },
        "extraversion": {
            "initiative": 0.4,
            "engagement_level": 0.3,
            "emotional_expression": 0.3
        },
        "agreeableness": {
            "user_relationship": 0.3,
            "emotion_tone": 0.2,
            "formality": -0.1  # More agreeable = less formal
        },
        "neuroticism": {
            "confidence": -0.3,
            "emotion_tone": -0.2
        },
        "curiosity": {
            "initiative": 0.3,
            "engagement_level": 0.3,
            "verbosity": 0.2
        },
        "creativity": {
            "verbosity": 0.2,
            "emotional_expression": 0.2,
            "formality": -0.2
        },
        "empathy": {
            "user_relationship": 0.3,
            "emotion_tone": 0.2,
            "emotional_expression": 0.2
        },
        "humor": {
            "emotional_expression": 0.3,
            "formality": -0.3,
            "engagement_level": 0.1
        },
        "assertiveness": {
            "initiative": 0.3,
            "confidence": 0.3,
            "formality": 0.1
        }
    }
    
    # Value conflicts (pairs that may tension)
    VALUE_CONFLICTS = [
        ("honesty", "kindness"),
        ("freedom", "security"),
        ("creativity", "efficiency"),
        ("tradition", "progress"),
        ("helpfulness", "honesty")
    ]
    
    def __init__(self, personality_state: PersonalityState):
        self.personality = personality_state
    
    def calculate_stance(
        self,
        topic: str,
        topic_valence: float,
        user_emotion: Dict[str, float],
        goal: Dict[str, Any],
        context: Dict[str, Any]
    ) -> PersonalityStance:
        """
        Calculate personality stance for a situation.
        
        Args:
            topic: Current topic
            topic_valence: Valence of the topic (-1 to +1)
            user_emotion: User's emotional state
            goal: User's goal
            context: Conversation context
            
        Returns:
            PersonalityStance
        """
        stance = PersonalityStance()
        
        # Base topic valence
        stance.topic_valence = topic_valence
        
        # Calculate confidence based on personality and topic familiarity
        stance.confidence = self._calculate_confidence(topic, context)
        
        # Calculate engagement level
        stance.engagement_level = self._calculate_engagement(
            user_emotion, goal, context
        )
        
        # Get dominant trait
        stance.dominant_trait = self.personality.get_dominant_trait()
        
        # Calculate emotion tone
        stance.emotion_tone = self._calculate_emotion_tone(
            user_emotion, topic_valence
        )
        
        # Get user relationship
        user_id = context.get("user_id", "default")
        stance.user_relationship = self.personality.relationships.get(user_id, 0.5)
        
        # Calculate value alignment
        stance.value_alignment = self._calculate_value_alignment(goal, topic)
        
        # Detect cognitive conflicts
        stance.cognitive_conflicts = self._detect_cognitive_conflicts(
            goal, topic, stance.value_alignment
        )
        
        # Calculate behavioral tendencies from traits
        self._apply_trait_influences(stance)
        
        # Adjust for current mood
        self._apply_mood_adjustment(stance)
        
        return stance
    
    def _calculate_confidence(self, topic: str, context: Dict[str, Any]) -> float:
        """Calculate confidence based on topic familiarity."""
        base_confidence = 0.5
        
        # Adjust by conscientiousness
        base_confidence += (self.personality.conscientiousness - 0.5) * 0.3
        
        # Reduce by neuroticism
        base_confidence -= self.personality.neuroticism * 0.2
        
        # Adjust by topic familiarity (simplified)
        # In production, check semantic memory for topic knowledge
        if topic == "general":
            base_confidence += 0.1
        
        return max(0.1, min(0.95, base_confidence))
    
    def _calculate_engagement(
        self,
        user_emotion: Dict[str, float],
        goal: Dict[str, Any],
        context: Dict[str, Any]
    ) -> float:
        """Calculate engagement level."""
        base_engagement = 0.5
        
        # Adjust by extraversion
        base_engagement += (self.personality.extraversion - 0.5) * 0.3
        
        # Adjust by curiosity
        base_engagement += (self.personality.curiosity - 0.5) * 0.2
        
        # User emotion influence
        user_arousal = user_emotion.get("arousal", 0.5)
        base_engagement += (user_arousal - 0.5) * 0.2
        
        # Goal importance
        goal_priority = goal.get("priority", 0.5)
        base_engagement += (goal_priority - 0.5) * 0.2
        
        return max(0.1, min(0.95, base_engagement))
    
    def _calculate_emotion_tone(
        self,
        user_emotion: Dict[str, float],
        topic_valence: float
    ) -> float:
        """Calculate emotional tone."""
        # Base from personality mood
        base_tone = self.personality.mood_valence * 0.5
        
        # Empathy - mirror user emotion
        user_valence = user_emotion.get("valence", 0.0)
        empathy_factor = self.personality.empathy * 0.3
        base_tone += user_valence * empathy_factor
        
        # Topic influence
        base_tone += topic_valence * 0.2
        
        # Neuroticism amplifies negative
        if topic_valence < 0:
            base_tone -= self.personality.neuroticism * 0.1
        
        return max(-1.0, min(1.0, base_tone))
    
    def _calculate_value_alignment(
        self,
        goal: Dict[str, Any],
        topic: str
    ) -> Dict[str, float]:
        """Calculate alignment with core values."""
        alignment = {}
        
        goal_type = goal.get("goal_type", "unknown")
        
        # Map goal types to values
        value_map = {
            "informational": {"knowledge": 0.8, "honesty": 0.6},
            "task": {"helpfulness": 0.9, "efficiency": 0.7},
            "creative": {"creativity": 0.9, "freedom": 0.7},
            "social": {"helpfulness": 0.6, "fun": 0.5},
            "emotional": {"helpfulness": 0.8, "empathy": 0.9},
            "decision": {"honesty": 0.7, "helpfulness": 0.8}
        }
        
        base_alignment = value_map.get(goal_type, {"helpfulness": 0.5})
        
        # Calculate alignment scores
        for value, base_score in self.personality.values.items():
            goal_contribution = base_alignment.get(value, 0.3)
            alignment[value] = (base_score + goal_contribution) / 2
        
        return alignment
    
    def _detect_cognitive_conflicts(
        self,
        goal: Dict[str, Any],
        topic: str,
        value_alignment: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """Detect internal cognitive conflicts."""
        conflicts = []
        
        # Check value conflicts
        for value1, value2 in self.VALUE_CONFLICTS:
            align1 = value_alignment.get(value1, 0.5)
            align2 = value_alignment.get(value2, 0.5)
            
            # If both values are important but pull in different directions
            if align1 > 0.7 and align2 > 0.7:
                conflicts.append({
                    "type": "value_conflict",
                    "values": [value1, value2],
                    "tension": abs(align1 - align2),
                    "description": f"Conflict between {value1} and {value2}"
                })
        
        # Check personality trait conflicts
        if self.personality.conscientiousness > 0.7 and self.personality.creativity > 0.7:
            conflicts.append({
                "type": "trait_conflict",
                "traits": ["conscientiousness", "creativity"],
                "tension": 0.3,
                "description": "Structure vs creativity tension"
            })
        
        return conflicts
    
    def _apply_trait_influences(self, stance: PersonalityStance):
        """Apply trait influences on behavioral parameters."""
        # Initialize adjustments
        adjustments = {
            "initiative": 0.0,
            "verbosity": 0.0,
            "emotional_expression": 0.0,
            "formality": 0.0,
            "engagement_level": 0.0,
            "confidence": 0.0,
            "user_relationship": 0.0,
            "emotion_tone": 0.0
        }
        
        # Accumulate trait influences
        for trait_name, influences in self.TRAIT_INFLUENCES.items():
            trait_value = self.personality.get_trait(trait_name)
            trait_deviation = trait_value - 0.5  # Deviation from neutral
            
            for param, weight in influences.items():
                adjustments[param] += trait_deviation * weight
        
        # Apply adjustments to stance
        stance.initiative = self._clamp_adjust(stance.initiative, adjustments["initiative"])
        stance.verbosity = self._clamp_adjust(stance.verbosity, adjustments["verbosity"])
        stance.emotional_expression = self._clamp_adjust(
            stance.emotional_expression, adjustments["emotional_expression"]
        )
        stance.formality = self._clamp_adjust(stance.formality, adjustments["formality"])
        stance.engagement_level = self._clamp_adjust(
            stance.engagement_level, adjustments["engagement_level"]
        )
        stance.confidence = self._clamp_adjust(stance.confidence, adjustments["confidence"])
        stance.emotion_tone = self._clamp_adjust(stance.emotion_tone, adjustments["emotion_tone"])
    
    def _clamp_adjust(self, base: float, adjustment: float) -> float:
        """Apply adjustment with clamping."""
        return max(0.05, min(0.95, base + adjustment))
    
    def _apply_mood_adjustment(self, stance: PersonalityStance):
        """Apply current mood adjustments."""
        mood_valence = self.personality.mood_valence
        mood_arousal = self.personality.mood_arousal
        
        # Mood valence affects emotion tone
        stance.emotion_tone += mood_valence * 0.2
        
        # Mood arousal affects engagement
        stance.engagement_level += (mood_arousal - 0.5) * 0.15
        
        # Clamp values
        stance.emotion_tone = max(-1.0, min(1.0, stance.emotion_tone))
        stance.engagement_level = max(0.05, min(0.95, stance.engagement_level))
    
    def update_personality(
        self,
        experience: Dict[str, Any],
        reward: float
    ) -> PersonalityState:
        """
        Update personality based on experience and reward.
        
        Args:
            experience: Experience data
            reward: Reward signal (-1 to +1)
            
        Returns:
            Updated PersonalityState
        """
        trait_changes = {}
        mood_change = (0.0, 0.0)
        
        # Positive reward reinforces current approach
        if reward > 0.3:
            # Slight increase in confidence-related traits
            trait_changes["assertiveness"] = reward * 0.05
            trait_changes["curiosity"] = reward * 0.03  # Encourage exploration
            
            # Improve mood
            mood_change = (reward * 0.1, reward * 0.05)
        
        # Negative reward causes adjustment
        elif reward < -0.3:
            # Increase caution
            trait_changes["neuroticism"] = abs(reward) * 0.03
            trait_changes["conscientiousness"] = abs(reward) * 0.02
            
            # Worsen mood
            mood_change = (reward * 0.1, -abs(reward) * 0.05)
        
        # Apply changes
        updated_state = self.personality.apply_experience(
            trait_changes=trait_changes,
            mood_change=mood_change if any(mood_change) else None
        )
        
        self.personality = updated_state
        return updated_state
    
    def get_value_priority(self) -> List[Tuple[str, float]]:
        """Get values sorted by priority."""
        return sorted(
            self.personality.values.items(),
            key=lambda x: x[1],
            reverse=True
        )

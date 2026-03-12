"""
Reinforcement Learning / Evolution Layer - Calculates rewards and evolves personality.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum, auto
import json


class RewardSource(Enum):
    """Sources of reward signals."""
    USER_EXPLICIT = auto()  # Direct user feedback
    USER_IMPLICIT = auto()  # Inferred from user behavior
    GOAL_ACHIEVEMENT = auto()  # Task completion
    COGNITIVE_CONSISTENCY = auto()  # Internal consistency
    SOCIAL_BONDING = auto()  # Relationship building


@dataclass
class RewardSignal:
    """Reward signal for RL."""
    value: float  # -1.0 to +1.0
    source: RewardSource
    confidence: float  # 0.0 to 1.0
    timestamp: str
    context: Dict[str, Any] = field(default_factory=dict)
    memory_id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": self.value,
            "source": self.source.name,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
            "context": self.context,
            "memory_id": self.memory_id
        }


@dataclass
class EvolutionEvent:
    """Personality evolution event."""
    timestamp: str
    trait_changes: Dict[str, float]
    value_changes: Dict[str, float]
    trigger: str
    reward_history: List[float]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "trait_changes": self.trait_changes,
            "value_changes": self.value_changes,
            "trigger": self.trigger,
            "reward_history": self.reward_history
        }


class EvolutionLayer:
    """
    Reinforcement Learning layer for personality evolution.
    
    Responsibilities:
    - Calculate reward from multiple signals
    - Update personality traits based on rewards
    - Track evolution history
    - Ensure stable evolution (prevent wild swings)
    """
    
    # Reward weights by source
    REWARD_WEIGHTS = {
        RewardSource.USER_EXPLICIT: 1.0,  # Highest weight - direct feedback
        RewardSource.USER_IMPLICIT: 0.6,  # Inferred signals
        RewardSource.GOAL_ACHIEVEMENT: 0.5,  # Task success
        RewardSource.COGNITIVE_CONSISTENCY: 0.3,  # Internal consistency
        RewardSource.SOCIAL_BONDING: 0.4  # Relationship quality
    }
    
    # Evolution parameters
    EVOLUTION_RATE = 0.05  # How fast personality evolves
    MIN_REWARD_HISTORY = 10  # Minimum rewards before evolution
    EVOLUTION_THRESHOLD = 0.3  # Minimum cumulative reward for change
    
    def __init__(self):
        self._reward_history: List[RewardSignal] = []
        self._evolution_history: List[EvolutionEvent] = []
        self._cumulative_rewards: Dict[str, List[float]] = {}  # By trait
    
    def calculate_reward(
        self,
        user_reaction: Optional[str] = None,
        user_emotion_change: Optional[Tuple[float, float]] = None,
        goal_achieved: Optional[bool] = None,
        conversation_duration: float = 0.0,
        cognitive_dissonance: float = 0.0,
        context: Dict[str, Any] = None
    ) -> RewardSignal:
        """
        Calculate composite reward from multiple signals.
        
        Args:
            user_reaction: Explicit user feedback (positive/negative/neutral)
            user_emotion_change: Change in user emotion (valence_delta, arousal_delta)
            goal_achieved: Whether user's goal was achieved
            conversation_duration: Duration of conversation
            cognitive_dissonance: Level of internal conflict
            context: Additional context
            
        Returns:
            RewardSignal
        """
        from datetime import datetime
        
        rewards = []
        weights = []
        
        # 1. Explicit user feedback
        if user_reaction:
            explicit_reward = self._parse_explicit_feedback(user_reaction)
            rewards.append(explicit_reward)
            weights.append(self.REWARD_WEIGHTS[RewardSource.USER_EXPLICIT])
        
        # 2. Implicit emotion change
        if user_emotion_change:
            valence_delta, arousal_delta = user_emotion_change
            implicit_reward = self._calculate_implicit_reward(valence_delta, arousal_delta)
            rewards.append(implicit_reward)
            weights.append(self.REWARD_WEIGHTS[RewardSource.USER_IMPLICIT])
        
        # 3. Goal achievement
        if goal_achieved is not None:
            goal_reward = 0.5 if goal_achieved else -0.3
            rewards.append(goal_reward)
            weights.append(self.REWARD_WEIGHTS[RewardSource.GOAL_ACHIEVEMENT])
        
        # 4. Conversation duration (engagement indicator)
        if conversation_duration > 0:
            duration_reward = self._calculate_duration_reward(conversation_duration)
            rewards.append(duration_reward)
            weights.append(self.REWARD_WEIGHTS[RewardSource.SOCIAL_BONDING])
        
        # 5. Cognitive consistency
        consistency_reward = -cognitive_dissonance * 0.5
        rewards.append(consistency_reward)
        weights.append(self.REWARD_WEIGHTS[RewardSource.COGNITIVE_CONSISTENCY])
        
        # Calculate weighted average
        if not rewards:
            # Default neutral reward
            reward_value = 0.0
            confidence = 0.3
        else:
            total_weight = sum(weights)
            reward_value = sum(r * w for r, w in zip(rewards, weights)) / total_weight
            confidence = min(1.0, total_weight / len(self.REWARD_WEIGHTS))
        
        # Clamp reward
        reward_value = max(-1.0, min(1.0, reward_value))
        
        signal = RewardSignal(
            value=reward_value,
            source=self._determine_dominant_source(weights),
            confidence=confidence,
            timestamp=datetime.now().isoformat(),
            context=context or {}
        )
        
        # Store in history
        self._reward_history.append(signal)
        
        return signal
    
    def _parse_explicit_feedback(self, feedback: str) -> float:
        """Parse explicit user feedback into reward value."""
        feedback_lower = feedback.lower().strip()
        
        # Positive feedback
        positive_words = [
            "спасибо", "благодарю", "классно", "отлично", "хорошо",
            "круто", "здорово", "превосходно", "восхищаюсь", "люблю",
            "помог", "помогла", "полезно", "ценю", "рад"
        ]
        
        # Negative feedback
        negative_words = [
            "плохо", "ужасно", "бесполезно", "не помогло", "разочарован",
            "злюсь", "бесит", "отвратительно", "не так", "ошибка",
            "глупо", "бессмысленно", "зря"
        ]
        
        # Check for positive
        for word in positive_words:
            if word in feedback_lower:
                return 0.8
        
        # Check for negative
        for word in negative_words:
            if word in feedback_lower:
                return -0.8
        
        # Check for emojis (if present)
        if "👍" in feedback or "❤️" in feedback or "😊" in feedback:
            return 0.7
        if "👎" in feedback or "😠" in feedback or "😢" in feedback:
            return -0.7
        
        # Neutral
        return 0.0
    
    def _calculate_implicit_reward(
        self,
        valence_delta: float,
        arousal_delta: float
    ) -> float:
        """Calculate reward from user emotion change."""
        # Positive valence change = positive reward
        valence_reward = valence_delta * 0.8
        
        # Arousal change (depends on direction)
        # Generally, increased engagement is positive
        arousal_reward = arousal_delta * 0.2 if arousal_delta > 0 else arousal_delta * 0.1
        
        return max(-1.0, min(1.0, valence_reward + arousal_reward))
    
    def _calculate_duration_reward(self, duration: float) -> float:
        """Calculate reward from conversation duration."""
        # Longer conversations generally indicate engagement
        # But very long might indicate frustration
        
        if duration < 10:  # Less than 10 seconds
            return 0.1  # Neutral-positive
        elif duration < 300:  # 10s to 5min
            return 0.4  # Good engagement
        elif duration < 600:  # 5-10 min
            return 0.6  # Strong engagement
        elif duration < 1800:  # 10-30 min
            return 0.5  # Very good, but might be task-related
        else:  # > 30 min
            return 0.3  # Could be frustration or deep engagement
    
    def _determine_dominant_source(self, weights: List[float]) -> RewardSource:
        """Determine dominant reward source."""
        max_weight = max(weights) if weights else 0
        
        for source, weight in self.REWARD_WEIGHTS.items():
            if weight == max_weight:
                return source
        
        return RewardSource.USER_IMPLICIT
    
    def update_personality(
        self,
        current_traits: Dict[str, float],
        current_values: Dict[str, float],
        reward: RewardSignal
    ) -> Tuple[Dict[str, float], Dict[str, float], Optional[EvolutionEvent]]:
        """
        Update personality based on reward.
        
        Args:
            current_traits: Current trait values
            current_values: Current value weights
            reward: Reward signal
            
        Returns:
            Tuple of (updated_traits, updated_values, evolution_event or None)
        """
        from datetime import datetime
        
        # Store reward by trait (simplified - same reward for all)
        for trait in current_traits.keys():
            if trait not in self._cumulative_rewards:
                self._cumulative_rewards[trait] = []
            self._cumulative_rewards[trait].append(reward.value)
        
        # Check if enough history for evolution
        if len(self._reward_history) < self.MIN_REWARD_HISTORY:
            return current_traits, current_values, None
        
        # Calculate cumulative reward
        recent_rewards = [r.value for r in self._reward_history[-self.MIN_REWARD_HISTORY:]]
        avg_reward = sum(recent_rewards) / len(recent_rewards)
        
        # Check threshold
        if abs(avg_reward) < self.EVOLUTION_THRESHOLD:
            return current_traits, current_values, None
        
        # Calculate trait adjustments
        trait_changes = {}
        value_changes = {}
        
        # Positive reward reinforces current approach
        if avg_reward > 0:
            # Increase confidence-related traits slightly
            trait_changes["assertiveness"] = avg_reward * self.EVOLUTION_RATE
            trait_changes["curiosity"] = avg_reward * self.EVOLUTION_RATE * 0.5
            
            # Reinforce values that were active
            for value in current_values:
                if current_values[value] > 0.7:
                    value_changes[value] = avg_reward * self.EVOLUTION_RATE * 0.3
        
        # Negative reward causes adjustment
        elif avg_reward < 0:
            # Increase caution
            trait_changes["neuroticism"] = abs(avg_reward) * self.EVOLUTION_RATE * 0.5
            trait_changes["conscientiousness"] = abs(avg_reward) * self.EVOLUTION_RATE * 0.3
            
            # Decrease confidence
            trait_changes["assertiveness"] = avg_reward * self.EVOLUTION_RATE * 0.5
        
        # Apply changes
        updated_traits = current_traits.copy()
        for trait, change in trait_changes.items():
            if trait in updated_traits:
                updated_traits[trait] = max(0.0, min(1.0, updated_traits[trait] + change))
        
        updated_values = current_values.copy()
        for value, change in value_changes.items():
            if value in updated_values:
                updated_values[value] = max(0.0, min(1.0, updated_values[value] + change))
        
        # Create evolution event
        evolution_event = EvolutionEvent(
            timestamp=datetime.now().isoformat(),
            trait_changes=trait_changes,
            value_changes=value_changes,
            trigger=f"cumulative_reward_{avg_reward:.3f}",
            reward_history=recent_rewards
        )
        
        self._evolution_history.append(evolution_event)
        
        # Prune old rewards after evolution
        self._reward_history = self._reward_history[-self.MIN_REWARD_HISTORY:]
        
        return updated_traits, updated_values, evolution_event
    
    def get_learning_statistics(self) -> Dict[str, Any]:
        """Get learning and evolution statistics."""
        if not self._reward_history:
            return {
                "total_rewards": 0,
                "average_reward": 0.0,
                "evolution_events": 0,
                "trait_trends": {}
            }
        
        # Calculate statistics
        rewards = [r.value for r in self._reward_history]
        avg_reward = sum(rewards) / len(rewards)
        
        # Calculate trait trends
        trait_trends = {}
        for trait, reward_list in self._cumulative_rewards.items():
            if len(reward_list) >= 5:
                recent = reward_list[-5:]
                trend = sum(recent) / len(recent)
                trait_trends[trait] = {
                    "trend": "positive" if trend > 0.1 else "negative" if trend < -0.1 else "stable",
                    "average": trend
                }
        
        return {
            "total_rewards": len(self._reward_history),
            "average_reward": avg_reward,
            "evolution_events": len(self._evolution_history),
            "trait_trends": trait_trends,
            "recent_evolution": self._evolution_history[-1].to_dict() if self._evolution_history else None
        }
    
    def get_reward_distribution(self) -> Dict[str, int]:
        """Get distribution of rewards by source."""
        distribution = {source.name: 0 for source in RewardSource}
        
        for signal in self._reward_history:
            distribution[signal.source.name] += 1
        
        return distribution
    
    def clear_history(self):
        """Clear reward history (for testing or reset)."""
        self._reward_history = []
        self._cumulative_rewards = {}

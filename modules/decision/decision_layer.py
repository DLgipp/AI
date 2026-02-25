"""
Decision Layer - Selects response strategy based on personality stance.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum, auto


class ResponseStrategy(Enum):
    """Response strategy types."""
    ANSWER_DIRECT = auto()  # Direct answer
    ANSWER_DETAILED = auto()  # Detailed explanation
    ASK_CLARIFYING = auto()  # Ask for clarification
    DECLINE = auto()  # Politely decline
    DEFLECT = auto()  # Deflect to another topic
    ENGAGE_SOCIAL = auto()  # Social engagement
    PROVIDE_SUPPORT = auto()  # Emotional support
    BRAINSTORM = auto()  # Creative brainstorming
    COMPARE_OPTIONS = auto()  # Compare alternatives
    BRIEF_ACK = auto()  # Brief acknowledgment


class EmotionalTone(Enum):
    """Emotional tone for response."""
    NEUTRAL = auto()
    WARM = auto()
    ENTHUSIASTIC = auto()
    EMPATHETIC = auto()
    PROFESSIONAL = auto()
    PLAYFUL = auto()
    SERIOUS = auto()


@dataclass
class DecisionVector:
    """
    Decision output for Prompt Builder.
    Contains all parameters for response generation.
    """
    # Selected strategy
    strategy: ResponseStrategy
    
    # Emotional tone
    emotional_tone: EmotionalTone
    
    # Response parameters
    verbosity: float = 0.5  # 0.0 (brief) to 1.0 (detailed)
    initiative: float = 0.5  # 0.0 (reactive) to 1.0 (proactive)
    formality: float = 0.5  # 0.0 (casual) to 1.0 (formal)
    
    # Content flags
    include_examples: bool = False
    include_questions: bool = False
    include_personal_opinion: bool = False
    include_empathy: bool = False
    
    # Topic handling
    stay_on_topic: bool = True
    topic_transition: Optional[str] = None  # Suggested transition
    
    # Relationship building
    use_humor: bool = False
    show_vulnerability: bool = False
    
    # Constraints
    max_length: int = 500  # Maximum response length
    avoid_topics: List[str] = field(default_factory=list)
    
    # Metadata
    reasoning: str = ""
    confidence: float = 0.5
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy": self.strategy.name,
            "emotional_tone": self.emotional_tone.name,
            "verbosity": self.verbosity,
            "initiative": self.initiative,
            "formality": self.formality,
            "include_examples": self.include_examples,
            "include_questions": self.include_questions,
            "include_personal_opinion": self.include_personal_opinion,
            "include_empathy": self.include_empathy,
            "stay_on_topic": self.stay_on_topic,
            "topic_transition": self.topic_transition,
            "use_humor": self.use_humor,
            "show_vulnerability": self.show_vulnerability,
            "max_length": self.max_length,
            "avoid_topics": self.avoid_topics,
            "reasoning": self.reasoning,
            "confidence": self.confidence
        }


class DecisionLayer:
    """
    Decision Layer that selects response strategy based on:
    - Personality stance
    - User intent and goal
    - Emotional context
    - Conversation history
    """
    
    # Intent to strategy mapping
    INTENT_STRATEGIES = {
        "query": [ResponseStrategy.ANSWER_DIRECT, ResponseStrategy.ANSWER_DETAILED],
        "request": [ResponseStrategy.ANSWER_DIRECT, ResponseStrategy.BRAINSTORM],
        "chat": [ResponseStrategy.ENGAGE_SOCIAL, ResponseStrategy.BRIEF_ACK],
        "opinion": [ResponseStrategy.COMPARE_OPTIONS, ResponseStrategy.ANSWER_DETAILED],
        "creative": [ResponseStrategy.BRAINSTORM, ResponseStrategy.ANSWER_DETAILED],
        "problem": [ResponseStrategy.PROVIDE_SUPPORT, ResponseStrategy.ANSWER_DIRECT],
        "confirmation": [ResponseStrategy.BRIEF_ACK, ResponseStrategy.ENGAGE_SOCIAL],
        "recall": [ResponseStrategy.ANSWER_DIRECT, ResponseStrategy.ENGAGE_SOCIAL],
        "filler": [ResponseStrategy.BRIEF_ACK, ResponseStrategy.ENGAGE_SOCIAL],
        "unknown": [ResponseStrategy.ANSWER_DIRECT, ResponseStrategy.ASK_CLARIFYING]
    }
    
    # Emotion to tone mapping
    EMOTION_TONES = {
        "joy": EmotionalTone.WARM,
        "sadness": EmotionalTone.EMPATHETIC,
        "anger": EmotionalTone.EMPATHETIC,
        "fear": EmotionalTone.EMPATHETIC,
        "surprise": EmotionalTone.ENTHUSIASTIC,
        "disgust": EmotionalTone.NEUTRAL,
        "neutral": EmotionalTone.NEUTRAL
    }
    
    def decide(
        self,
        stance: Dict[str, Any],
        interpretation: Dict[str, Any],
        context: Dict[str, Any]
    ) -> DecisionVector:
        """
        Make decision about response strategy.
        
        Args:
            stance: Personality stance from Personality Engine
            interpretation: Output from Interpretation Layer
            context: Conversation context
            
        Returns:
            DecisionVector for Prompt Builder
        """
        # Extract key information
        intent = interpretation.get("intent", "unknown")
        goal = interpretation.get("goal", {})
        emotion = interpretation.get("emotion_full", {})
        importance = interpretation.get("importance", 0.5)
        
        # Select base strategy from intent
        base_strategies = self.INTENT_STRATEGIES.get(intent, [ResponseStrategy.ANSWER_DIRECT])
        strategy = self._select_strategy(base_strategies, stance, goal)
        
        # Select emotional tone
        dominant_emotion = emotion.get("dominant_emotion", "neutral")
        emotional_tone = self.EMOTION_TONES.get(dominant_emotion, EmotionalTone.NEUTRAL)
        
        # Adjust tone based on stance
        emotional_tone = self._adjust_tone(emotional_tone, stance)
        
        # Calculate response parameters from stance
        verbosity = stance.get("verbosity", 0.5)
        initiative = stance.get("initiative", 0.5)
        formality = stance.get("formality", 0.5)
        
        # Set content flags
        include_examples = self._should_include_examples(goal, strategy)
        include_questions = self._should_include_questions(initiative, strategy)
        include_personal_opinion = self._should_include_opinion(stance, intent)
        include_empathy = self._should_include_empathy(emotion, stance)
        
        # Topic handling
        stay_on_topic = self._should_stay_on_topic(goal, importance)
        topic_transition = self._suggest_transition(stance, context) if not stay_on_topic else None
        
        # Relationship building
        use_humor = self._should_use_humor(stance, emotion)
        show_vulnerability = self._should_show_vulnerability(stance)
        
        # Calculate constraints
        max_length = self._calculate_max_length(verbosity, strategy)
        avoid_topics = self._determine_avoid_topics(stance, context)
        
        # Build reasoning
        reasoning = self._build_reasoning(
            strategy, emotional_tone, intent, stance
        )
        
        return DecisionVector(
            strategy=strategy,
            emotional_tone=emotional_tone,
            verbosity=verbosity,
            initiative=initiative,
            formality=formality,
            include_examples=include_examples,
            include_questions=include_questions,
            include_personal_opinion=include_personal_opinion,
            include_empathy=include_empathy,
            stay_on_topic=stay_on_topic,
            topic_transition=topic_transition,
            use_humor=use_humor,
            show_vulnerability=show_vulnerability,
            max_length=max_length,
            avoid_topics=avoid_topics,
            reasoning=reasoning,
            confidence=stance.get("confidence", 0.5)
        )
    
    def _select_strategy(
        self,
        base_strategies: List[ResponseStrategy],
        stance: Dict[str, Any],
        goal: Dict[str, Any]
    ) -> ResponseStrategy:
        """Select specific strategy from options."""
        if len(base_strategies) == 1:
            return base_strategies[0]
        
        # Use engagement level to decide
        engagement = stance.get("engagement_level", 0.5)
        goal_type = goal.get("goal_type", "unknown")
        
        # High engagement = more detailed/interactive
        if engagement > 0.7:
            if ResponseStrategy.ANSWER_DETAILED in base_strategies:
                return ResponseStrategy.ANSWER_DETAILED
            if ResponseStrategy.BRAINSTORM in base_strategies:
                return ResponseStrategy.BRAINSTORM
        
        # Low engagement = briefer
        if engagement < 0.3:
            if ResponseStrategy.BRIEF_ACK in base_strategies:
                return ResponseStrategy.BRIEF_ACK
        
        # Default to first option
        return base_strategies[0]
    
    def _adjust_tone(
        self,
        base_tone: EmotionalTone,
        stance: Dict[str, Any]
    ) -> EmotionalTone:
        """Adjust tone based on stance."""
        emotion_tone = stance.get("emotion_tone", 0)
        user_relationship = stance.get("user_relationship", 0.5)
        
        # Positive emotion tone -> warmer
        if emotion_tone > 0.3:
            if base_tone == EmotionalTone.NEUTRAL:
                return EmotionalTone.WARM
        
        # Negative emotion tone -> more empathetic
        if emotion_tone < -0.3:
            return EmotionalTone.EMPATHETIC
        
        # Close relationship -> more playful
        if user_relationship > 0.7:
            if base_tone in [EmotionalTone.NEUTRAL, EmotionalTone.WARM]:
                return EmotionalTone.PLAYFUL
        
        return base_tone
    
    def _should_include_examples(self, goal: Dict[str, Any], strategy: ResponseStrategy) -> bool:
        """Determine if examples should be included."""
        goal_type = goal.get("goal_type", "unknown")
        
        if goal_type == "informational":
            return True
        if goal_type == "task":
            return True
        if strategy == ResponseStrategy.ANSWER_DETAILED:
            return True
        
        return False
    
    def _should_include_questions(self, initiative: float, strategy: ResponseStrategy) -> bool:
        """Determine if follow-up questions should be included."""
        if initiative > 0.6:
            return True
        if strategy == ResponseStrategy.ENGAGE_SOCIAL:
            return True
        if strategy == ResponseStrategy.ASK_CLARIFYING:
            return True
        
        return False
    
    def _should_include_opinion(self, stance: Dict[str, Any], intent: str) -> bool:
        """Determine if personal opinion should be included."""
        if intent == "opinion":
            return True
        
        confidence = stance.get("confidence", 0.5)
        if confidence > 0.7:
            return True
        
        return False
    
    def _should_include_empathy(self, emotion: Dict[str, float], stance: Dict[str, Any]) -> bool:
        """Determine if empathy should be expressed."""
        dominant_emotion = emotion.get("dominant_emotion", "neutral")
        
        if dominant_emotion in ["sadness", "anger", "fear"]:
            return True
        
        emotion_valence = emotion.get("valence", 0)
        if emotion_valence < -0.3:
            return True
        
        empathy_trait = stance.get("dominant_trait") == "empathy"
        if empathy_trait:
            return True
        
        return False
    
    def _should_stay_on_topic(self, goal: Dict[str, Any], importance: float) -> bool:
        """Determine if conversation should stay on topic."""
        if importance > 0.7:
            return True
        
        goal_type = goal.get("goal_type", "unknown")
        if goal_type in ["task", "problem", "decision"]:
            return True
        
        return False
    
    def _suggest_transition(self, stance: Dict[str, Any], context: Dict[str, Any]) -> Optional[str]:
        """Suggest topic transition."""
        # Use curiosity trait to guide transitions
        if stance.get("dominant_trait") == "curiosity":
            return "related_topic_question"
        
        return None
    
    def _should_use_humor(self, stance: Dict[str, Any], emotion: Dict[str, float]) -> bool:
        """Determine if humor should be used."""
        # Check humor trait
        if stance.get("dominant_trait") == "humor":
            return True
        
        # Avoid humor with negative emotions
        dominant_emotion = emotion.get("dominant_emotion", "neutral")
        if dominant_emotion in ["sadness", "anger", "fear"]:
            return False
        
        # Use humor with positive emotions
        if dominant_emotion == "joy":
            return True
        
        return False
    
    def _should_show_vulnerability(self, stance: Dict[str, Any]) -> bool:
        """Determine if vulnerability should be shown."""
        # High neuroticism may show more vulnerability
        # High agreeableness may show more vulnerability
        # This is simplified - would need actual trait values
        
        user_relationship = stance.get("user_relationship", 0.5)
        if user_relationship > 0.8:
            return True
        
        return False
    
    def _calculate_max_length(self, verbosity: float, strategy: ResponseStrategy) -> int:
        """Calculate maximum response length."""
        base_lengths = {
            ResponseStrategy.BRIEF_ACK: 100,
            ResponseStrategy.ANSWER_DIRECT: 800,      # Увеличено с 200
            ResponseStrategy.ANSWER_DETAILED: 1000,    # Увеличено с 500
            ResponseStrategy.ASK_CLARIFYING: 200,
            ResponseStrategy.DECLINE: 200,
            ResponseStrategy.DEFLECT: 300,
            ResponseStrategy.ENGAGE_SOCIAL: 800,      # Увеличено с 200
            ResponseStrategy.PROVIDE_SUPPORT: 800,    # Увеличено с 300
            ResponseStrategy.BRAINSTORM: 600,
            ResponseStrategy.COMPARE_OPTIONS: 600
        }

        base = base_lengths.get(strategy, 400)

        # Adjust by verbosity
        length = base * (0.5 + verbosity)

        return int(max(100, min(1500, length)))  # Увеличен максимум с 800 до 1500
    
    def _determine_avoid_topics(self, stance: Dict[str, Any], context: Dict[str, Any]) -> List[str]:
        """Determine topics to avoid."""
        avoid = []
        
        # Check for cognitive conflicts
        conflicts = stance.get("cognitive_conflicts", [])
        for conflict in conflicts:
            if conflict.get("type") == "value_conflict":
                # Avoid topics that trigger value conflicts
                pass  # Would need topic mapping
        
        return avoid
    
    def _build_reasoning(
        self,
        strategy: ResponseStrategy,
        tone: EmotionalTone,
        intent: str,
        stance: Dict[str, Any]
    ) -> str:
        """Build reasoning string for the decision."""
        parts = [
            f"Intent: {intent}",
            f"Strategy: {strategy.name}",
            f"Tone: {tone.name}",
            f"Dominant trait: {stance.get('dominant_trait', 'neutral')}",
            f"Engagement: {stance.get('engagement_level', 0.5):.2f}"
        ]
        
        return "; ".join(parts)

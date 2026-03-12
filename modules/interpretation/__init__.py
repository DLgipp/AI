"""
Interpretation Layer - Main module.
"""

from modules.interpretation.topic_detector import TopicDetector, TopicResult
from modules.interpretation.goal_extractor import GoalExtractor, GoalResult
from modules.interpretation.importance_scorer import ImportanceScorer, ImportanceResult

__all__ = [
    "TopicDetector",
    "TopicResult",
    "GoalExtractor",
    "GoalResult",
    "ImportanceScorer",
    "ImportanceResult"
]


class InterpretationLayer:
    """
    Unified Interpretation Layer that combines all interpretation modules.
    
    Input: Perception output
    Output: Structured interpretation for Memory and Personality layers
    """
    
    def __init__(self):
        self.topic_detector = TopicDetector()
        self.goal_extractor = GoalExtractor()
        self.importance_scorer = ImportanceScorer()
    
    def process(
        self,
        text: str,
        perception: dict = None,
        context: dict = None
    ) -> dict:
        """
        Process perception output through all interpretation modules.
        
        Args:
            text: Original input text
            perception: Output from Perception Layer
            context: Conversation context
            
        Returns:
            Structured interpretation output
        """
        # Extract components from perception
        emotion = perception.get("emotion", {}) if perception else {}
        intent = perception.get("intent", {}) if perception else {}
        intent_label = intent.get("intent", "unknown") if intent else "unknown"
        silence_duration = perception.get("perceived_input", {}).get("silence_duration", 0.0)
        
        # Step 1: Detect topic
        topic = self.topic_detector.detect(text)
        
        # Step 2: Extract goal
        goal = self.goal_extractor.extract(
            text=text,
            intent=intent_label,
            emotion=emotion
        )
        
        # Step 3: Calculate importance
        importance = self.importance_scorer.calculate(
            text=text,
            emotion=emotion,
            goal=goal.to_dict(),
            topic=topic.to_dict(),
            context=context,
            silence_duration=silence_duration
        )
        
        # Combine results
        return {
            "intent": intent_label,
            "topic_vector": topic.topic_vector,
            "topic": topic.to_dict(),
            "user_emotion": emotion.get("valence", 0.0),
            "emotion_full": emotion,
            "goal": goal.to_dict(),
            "importance": importance.importance,
            "importance_factors": importance.factors,
            "importance_reasoning": importance.reasoning
        }

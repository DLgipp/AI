"""
Personality Module - Main module.
"""

from modules.personality.personality_engine import PersonalityEngine, PersonalityStance
from modules.memory.personality_memory import PersonalityState, PersonalityMemoryStore

__all__ = [
    "PersonalityEngine",
    "PersonalityStance",
    "PersonalityState",
    "PersonalityMemoryStore",
    "PersonalityLayer"
]


class PersonalityLayer:
    """
    Unified Personality Layer that combines personality storage and engine.
    
    Responsibilities:
    - Maintain personality state
    - Calculate stance for each situation
    - Update personality based on experiences
    - Provide value alignment information
    """
    
    def __init__(self, db_path: str = "data/personality_memory.db"):
        self.memory = PersonalityMemoryStore(db_path)
        self.engine = None  # Initialized after loading state
        self._load_state()
    
    def _load_state(self):
        """Load personality state and initialize engine."""
        state = self.memory.get_state()
        self.engine = PersonalityEngine(state)
    
    def get_stance(
        self,
        topic: str,
        topic_valence: float,
        user_emotion: dict,
        goal: dict,
        context: dict
    ) -> PersonalityStance:
        """
        Calculate personality stance for current situation.
        
        Args:
            topic: Current topic
            topic_valence: Valence of topic (-1 to +1)
            user_emotion: User's emotional state
            goal: User's goal
            context: Conversation context
            
        Returns:
            PersonalityStance
        """
        return self.engine.calculate_stance(
            topic=topic,
            topic_valence=topic_valence,
            user_emotion=user_emotion,
            goal=goal,
            context=context
        )
    
    def get_state(self) -> PersonalityState:
        """Get current personality state."""
        return self.engine.personality
    
    def update_from_experience(
        self,
        experience: dict,
        reward: float
    ) -> PersonalityState:
        """
        Update personality based on experience.
        
        Args:
            experience: Experience data
            reward: Reward signal
            
        Returns:
            Updated PersonalityState
        """
        updated = self.engine.update_personality(experience, reward)
        self.memory.save_state(updated)
        return updated
    
    def update_relationship(self, user_id: str, score: float):
        """Update relationship with user."""
        self.memory.update_relationship(user_id, score)
        self._load_state()  # Reload to get updated engine
    
    def get_value_priority(self) -> list:
        """Get values sorted by priority."""
        return self.engine.get_value_priority()
    
    def get_dominant_trait(self) -> str:
        """Get dominant personality trait."""
        return self.engine.personality.get_dominant_trait()

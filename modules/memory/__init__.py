"""
Memory Layer - Main module providing unified access to all memory systems.
"""

from modules.memory.episodic_memory import EpisodicMemoryStore, EpisodicMemory
from modules.memory.semantic_memory import SemanticMemoryStore, SemanticMemory
from modules.memory.relational_memory import RelationalMemoryStore, Entity, Relation
from modules.memory.personality_memory import PersonalityMemoryStore, PersonalityState

__all__ = [
    "EpisodicMemoryStore",
    "EpisodicMemory",
    "SemanticMemoryStore",
    "SemanticMemory",
    "RelationalMemoryStore",
    "Entity",
    "Relation",
    "PersonalityMemoryStore",
    "PersonalityState",
    "MemoryLayer"
]


class MemoryLayer:
    """
    Unified Memory Layer that provides access to all memory systems.
    
    Coordinates between:
    - Episodic Memory (events, experiences)
    - Semantic Memory (knowledge, concepts)
    - Relational Memory (relationships, graph)
    - Personality Memory (traits, values, state)
    """
    
    def __init__(
        self,
        episodic_path: str = "data/episodic_memory.db",
        semantic_path: str = "data/semantic_memory.db",
        relational_path: str = "data/relational_memory.db",
        personality_path: str = "data/personality_memory.db"
    ):
        self.episodic = EpisodicMemoryStore(episodic_path)
        self.semantic = SemanticMemoryStore(semantic_path)
        self.relational = RelationalMemoryStore(relational_path)
        self.personality = PersonalityMemoryStore(personality_path)
    
    def store_experience(
        self,
        session_id: str,
        event_type: str,
        content: str,
        interpretation: dict,
        metadata: dict = None
    ) -> int:
        """
        Store a complete experience across all memory systems.
        
        Args:
            session_id: Session identifier
            event_type: Type of event (user_message, assistant_message, system_event)
            content: Main content
            interpretation: Output from Interpretation Layer
            metadata: Additional metadata
            
        Returns:
            Episodic memory ID
        """
        from datetime import datetime
        
        # Extract interpretation data
        emotion = interpretation.get("emotion_full", {})
        goal = interpretation.get("goal", {})
        topic = interpretation.get("topic", {})
        
        # Store in episodic memory
        memory_id = self.episodic.save(EpisodicMemory(
            id=None,
            session_id=session_id,
            timestamp=datetime.now().isoformat(),
            event_type=event_type,
            content=content,
            emotion_valence=emotion.get("valence", 0.0),
            emotion_arousal=emotion.get("arousal", 0.5),
            importance=interpretation.get("importance", 0.5),
            topic=topic.get("primary_topic", "general"),
            intent=interpretation.get("intent", "unknown"),
            goal=goal.get("goal", ""),
            metadata=metadata or {}
        ))
        
        # Store in semantic memory (extract knowledge)
        if interpretation.get("importance", 0.5) > 0.6:
            self.semantic.save(SemanticMemory(
                id=None,
                concept=topic.get("primary_topic", "general"),
                content=content,
                embedding=interpretation.get("topic_vector", [0.5] * 5),
                category=topic.get("category", "general"),
                tags=topic.get("keywords", []),
                importance=interpretation.get("importance", 0.5),
                source="conversation"
            ))
        
        # Update relational memory (entities and relationships)
        self._update_relational_memory(session_id, content, interpretation)
        
        return memory_id
    
    def _update_relational_memory(
        self,
        session_id: str,
        content: str,
        interpretation: dict
    ):
        """Update relational memory with entities and relationships."""
        # Extract potential entities (simplified)
        topic = interpretation.get("topic", {})
        goal = interpretation.get("goal", {})
        
        # Create entity for topic
        topic_name = topic.get("primary_topic", "general")
        if topic_name != "general":
            topic_entity = self.relational.get_entity(topic_name)
            if not topic_entity:
                self.relational.create_entity(Entity(
                    id=None,
                    name=topic_name,
                    entity_type="concept",
                    properties={
                        "category": topic.get("category", "general"),
                        "keywords": topic.get("keywords", [])
                    }
                ))
        
        # Create entity for goal
        goal_text = goal.get("goal", "")
        if goal_text and len(goal_text) > 5:
            goal_entity = self.relational.get_entity(f"goal:{goal_text[:50]}")
            if not goal_entity:
                self.relational.create_entity(Entity(
                    id=None,
                    name=f"goal:{goal_text[:50]}",
                    entity_type="goal",
                    properties={
                        "goal_type": goal.get("goal_type", "unknown"),
                        "full_text": goal_text
                    }
                ))
    
    def get_context(
        self,
        session_id: str,
        limit: int = 10
    ) -> dict:
        """
        Get relevant context for current interaction.
        
        Args:
            session_id: Session identifier
            limit: Number of recent memories to retrieve
            
        Returns:
            Dictionary with context from all memory systems
        """
        # Get recent episodic memories
        recent = self.episodic.get_recent(session_id=session_id, limit=limit)
        
        # Get personality state
        personality = self.personality.get_state()
        
        # Build context
        return {
            "recent_memories": [m.to_dict() for m in recent],
            "personality_state": personality.to_dict(),
            "conversation_turns": len(recent),
            "active_goal": None,  # Could be tracked separately
            "ongoing_task": None
        }
    
    def search_knowledge(
        self,
        query: str,
        query_embedding: list = None,
        limit: int = 5
    ) -> list:
        """
        Search semantic memory for relevant knowledge.
        
        Args:
            query: Search query text
            query_embedding: Optional query vector
            limit: Maximum results
            
        Returns:
            List of relevant memories
        """
        if query_embedding:
            results = self.semantic.search_by_vector(query_embedding, limit=limit)
            return [{"memory": m.to_dict(), "similarity": s} for m, s in results]
        else:
            # Simple text search
            memories = self.semantic.get_by_concept(query, limit=limit)
            return [{"memory": m.to_dict(), "similarity": 1.0} for m in memories]
    
    def get_relationship_context(self, user_id: str) -> dict:
        """
        Get relationship context for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Relationship context
        """
        score = self.personality.get_relationship(user_id)
        
        # Get shared history
        shared_memories = self.episodic.get_recent(limit=20)
        
        return {
            "relationship_score": score,
            "shared_memories_count": len(shared_memories),
            "recent_interactions": [m.to_dict() for m in shared_memories[:5]]
        }
    
    def update_from_feedback(
        self,
        memory_id: int,
        user_reaction: str,
        reward: float
    ):
        """
        Update memory based on user feedback (for RL).
        
        Args:
            memory_id: Episodic memory ID
            user_reaction: User's reaction
            reward: Calculated reward signal
        """
        # Update episodic memory with reaction
        self.episodic.update_user_reaction(memory_id, user_reaction)
        
        # Adjust importance based on reward
        if reward > 0.7:
            # High reward - increase importance
            memories = self.episodic.get_recent(limit=1)
            if memories:
                mem = memories[0]
                new_importance = min(1.0, mem.importance + 0.1)
                # Could update semantic memory importance too
    
    def get_statistics(self) -> dict:
        """Get overall memory statistics."""
        return {
            "episodic": self.episodic.get_statistics(),
            "semantic": self.semantic.get_statistics(),
            "relational": self.relational.get_statistics(),
            "personality": self.personality.get_statistics()
        }

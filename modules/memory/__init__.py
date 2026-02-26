"""
Memory Layer - Main module providing unified access to all memory systems.

Production Configuration:
- Episodic Memory: PostgreSQL
- Semantic Memory: Milvus (Vector DB)
- Relational Memory: Neo4j (Graph DB)
- Personality Memory: PostgreSQL
"""

from modules.memory.episodic_memory import EpisodicMemoryStore, EpisodicMemory, PostgreSQLEpisodicMemoryStore
from modules.memory.semantic_memory import SemanticMemoryStore, SemanticMemory, MilvusSemanticMemoryStore
from modules.memory.relational_memory import RelationalMemoryStore, Entity, Relation, Neo4jRelationalMemoryStore
from modules.memory.personality_memory import PersonalityState, PostgreSQLPersonalityMemoryStore

__all__ = [
    # Episodic
    "EpisodicMemoryStore",
    "EpisodicMemory",
    "PostgreSQLEpisodicMemoryStore",
    # Semantic
    "SemanticMemoryStore",
    "SemanticMemory",
    "MilvusSemanticMemoryStore",
    # Relational
    "RelationalMemoryStore",
    "Entity",
    "Relation",
    "Neo4jRelationalMemoryStore",
    # Personality
    "PersonalityState",
    "PostgreSQLPersonalityMemoryStore",
    # Main
    "MemoryLayer"
]


class MemoryLayer:
    """
    Unified Memory Layer that provides access to all memory systems.

    Production Configuration:
    - Episodic Memory: PostgreSQL (events, experiences)
    - Semantic Memory: Milvus Vector DB (knowledge, concepts)
    - Relational Memory: Neo4j Graph DB (relationships, graph)
    - Personality Memory: PostgreSQL (traits, values, state)

    Coordinates between all memory systems for complete experience storage.
    """

    def __init__(
        self,
        use_production_dbs: bool = True,
        episodic_db_url: str = None,
        personality_db_url: str = None,
        milvus_host: str = None,
        milvus_port: int = None,
        neo4j_uri: str = None,
        # Legacy SQLite paths for fallback
        episodic_path: str = "data/episodic_memory.db",
        semantic_path: str = "data/semantic_memory.db",
        relational_path: str = "data/relational_memory.db",
        personality_path: str = "data/personality_memory.db"
    ):
        """
        Initialize Memory Layer.

        Args:
            use_production_dbs: If True, use PostgreSQL/Milvus/Neo4j. If False, use SQLite.
            episodic_db_url: PostgreSQL URL for episodic memory
            personality_db_url: PostgreSQL URL for personality memory
            milvus_host: Milvus server host
            milvus_port: Milvus server port
            neo4j_uri: Neo4j connection URI
            episodic_path: SQLite path (fallback)
            semantic_path: SQLite path (fallback)
            relational_path: SQLite path (fallback)
            personality_path: SQLite path (fallback)
        """
        from config import (
            EPISODIC_DB_URL as CFG_EPISODIC_URL,
            PERSONALITY_DB_URL as CFG_PERSONALITY_URL,
            MILVUS_HOST as CFG_MILVUS_HOST,
            MILVUS_PORT as CFG_MILVUS_PORT,
            NEO4J_URI as CFG_NEO4J_URI
        )

        if use_production_dbs:
            # Use production databases
            self.episodic = PostgreSQLEpisodicMemoryStore(
                db_url=episodic_db_url or CFG_EPISODIC_URL
            )
            self.semantic = MilvusSemanticMemoryStore(
                host=milvus_host or CFG_MILVUS_HOST,
                port=milvus_port or CFG_MILVUS_PORT
            )
            self.relational = Neo4jRelationalMemoryStore(
                uri=neo4j_uri or CFG_NEO4J_URI
            )
            self.personality = PostgreSQLPersonalityMemoryStore(
                db_url=personality_db_url or CFG_PERSONALITY_URL
            )
            self._use_production = True
        else:
            # Use SQLite (fallback for development/debugging)
            self.episodic = EpisodicMemoryStore(episodic_path)
            self.semantic = SemanticMemoryStore(semantic_path)
            self.relational = RelationalMemoryStore(relational_path)
            self.personality = PersonalityMemoryStore(personality_path)
            self._use_production = False
    
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
            "personality": self._get_personality_statistics()
        }

    def _get_personality_statistics(self) -> dict:
        """Get personality statistics formatted for display."""
        stats = self.personality.get_statistics()
        # Convert top_values list to string for Rich compatibility
        if isinstance(stats.get('top_values'), list):
            stats['top_values'] = stats['top_values']  # Keep as list, will be formatted in display
        return stats

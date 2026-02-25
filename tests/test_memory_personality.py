"""
Tests for Memory and Personality modules.
"""

import unittest
import os
import tempfile
from modules.memory.episodic_memory import EpisodicMemoryStore, EpisodicMemory
from modules.memory.semantic_memory import SemanticMemoryStore, SemanticMemory
from modules.memory.personality_memory import PersonalityMemoryStore, PersonalityState
from modules.personality.personality_engine import PersonalityEngine, PersonalityStance


class TestEpisodicMemory(unittest.TestCase):
    """Tests for EpisodicMemoryStore."""
    
    def setUp(self):
        # Create temp database
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_file.close()
        self.store = EpisodicMemoryStore(self.temp_file.name)
    
    def tearDown(self):
        os.unlink(self.temp_file.name)
    
    def test_save_memory(self):
        """Test saving episodic memory."""
        memory = EpisodicMemory(
            id=None,
            session_id="test_session",
            timestamp="2024-01-01T00:00:00",
            event_type="user_message",
            content="Привет",
            emotion_valence=0.5,
            importance=0.7
        )
        
        memory_id = self.store.save(memory)
        self.assertGreater(memory_id, 0)
    
    def test_get_recent(self):
        """Test retrieving recent memories."""
        # Save some memories
        for i in range(5):
            self.store.save(EpisodicMemory(
                id=None,
                session_id="test",
                timestamp=f"2024-01-0{i}T00:00:00",
                event_type="user_message",
                content=f"Message {i}",
                importance=0.5 + i * 0.1
            ))
        
        recent = self.store.get_recent(session_id="test", limit=3)
        
        self.assertEqual(len(recent), 3)
    
    def test_get_by_topic(self):
        """Test retrieving memories by topic."""
        self.store.save(EpisodicMemory(
            id=None,
            session_id="test",
            timestamp="2024-01-01T00:00:00",
            event_type="user_message",
            content="About AI",
            topic="ai_ml"
        ))
        
        memories = self.store.get_by_topic("ai_ml")
        
        self.assertGreater(len(memories), 0)
        self.assertEqual(memories[0].topic, "ai_ml")


class TestSemanticMemory(unittest.TestCase):
    """Tests for SemanticMemoryStore."""
    
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_file.close()
        self.store = SemanticMemoryStore(self.temp_file.name)
    
    def tearDown(self):
        os.unlink(self.temp_file.name)
    
    def test_save_memory(self):
        """Test saving semantic memory."""
        memory = SemanticMemory(
            id=None,
            concept="искусственный интеллект",
            content="ИИ - это...",
            embedding=[0.8, 0.2, 0.3, 0.7, 0.4],
            category="technology"
        )
        
        memory_id = self.store.save(memory)
        self.assertGreater(memory_id, 0)
    
    def test_get_by_concept(self):
        """Test retrieving by concept."""
        self.store.save(SemanticMemory(
            id=None,
            concept="программирование",
            content="Python это язык...",
            embedding=[0.5] * 5
        ))
        
        memories = self.store.get_by_concept("программирование")
        
        self.assertGreater(len(memories), 0)
    
    def test_search_by_vector(self):
        """Test vector similarity search."""
        # Save memories with different embeddings
        self.store.save(SemanticMemory(
            id=None,
            concept="AI",
            content="Artificial Intelligence",
            embedding=[0.9, 0.1, 0.2, 0.8, 0.3],
            importance=0.8
        ))
        self.store.save(SemanticMemory(
            id=None,
            concept="Food",
            content="Delicious food",
            embedding=[0.1, 0.9, 0.8, 0.2, 0.1],
            importance=0.8
        ))
        
        # Search with AI-like vector
        results = self.store.search_by_vector(
            query_embedding=[0.85, 0.15, 0.2, 0.75, 0.3],
            limit=1
        )
        
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0][0].concept, "AI")


class TestPersonalityMemory(unittest.TestCase):
    """Tests for PersonalityMemoryStore."""
    
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_file.close()
        self.store = PersonalityMemoryStore(self.temp_file.name)
    
    def tearDown(self):
        os.unlink(self.temp_file.name)
    
    def test_get_state(self):
        """Test getting personality state."""
        state = self.store.get_state()
        
        self.assertIsInstance(state, PersonalityState)
        self.assertEqual(state.openness, 0.5)  # Default
    
    def test_update_trait(self):
        """Test updating a trait."""
        result = self.store.update_trait("curiosity", 0.8)
        
        self.assertTrue(result)
        
        state = self.store.get_state()
        self.assertEqual(state.curiosity, 0.8)
    
    def test_update_mood(self):
        """Test updating mood."""
        result = self.store.update_mood(valence=0.6, arousal=0.7)
        
        self.assertTrue(result)
        
        state = self.store.get_state()
        self.assertEqual(state.mood_valence, 0.6)
        self.assertEqual(state.mood_arousal, 0.7)
    
    def test_update_relationship(self):
        """Test updating relationship."""
        self.store.update_relationship("user1", 0.8)
        
        score = self.store.get_relationship("user1")
        self.assertEqual(score, 0.8)
    
    def test_get_dominant_trait(self):
        """Test getting dominant trait."""
        self.store.update_trait("curiosity", 0.9)
        self.store.update_trait("empathy", 0.8)
        
        state = self.store.get_state()
        dominant = state.get_dominant_trait()
        
        self.assertEqual(dominant, "curiosity")


class TestPersonalityEngine(unittest.TestCase):
    """Tests for PersonalityEngine."""
    
    def setUp(self):
        self.state = PersonalityState(
            openness=0.7,
            extraversion=0.6,
            curiosity=0.8,
            empathy=0.7
        )
        self.engine = PersonalityEngine(self.state)
    
    def test_calculate_stance(self):
        """Test stance calculation."""
        stance = self.engine.calculate_stance(
            topic="AI",
            topic_valence=0.5,
            user_emotion={"valence": 0.3, "arousal": 0.6},
            goal={"goal_type": "informational", "priority": 0.7},
            context={"user_id": "test"}
        )
        
        self.assertIsInstance(stance, PersonalityStance)
        self.assertGreater(stance.engagement_level, 0.5)  # High curiosity
    
    def test_get_value_priority(self):
        """Test value priority ordering."""
        priorities = self.engine.get_value_priority()
        
        self.assertIsInstance(priorities, list)
        self.assertGreater(priorities[0][1], priorities[-1][1])
    
    def test_update_personality_positive(self):
        """Test personality update with positive reward."""
        old_state = self.engine.personality
        
        new_state = self.engine.update_personality(
            experience={"type": "success"},
            reward=0.8
        )
        
        # Assertiveness should increase with positive reward
        self.assertGreater(new_state.assertiveness, old_state.assertiveness)
    
    def test_update_personality_negative(self):
        """Test personality update with negative reward."""
        old_state = self.engine.personality
        
        new_state = self.engine.update_personality(
            experience={"type": "failure"},
            reward=-0.8
        )
        
        # Neuroticism should increase with negative reward
        self.assertGreater(new_state.neuroticism, old_state.neuroticism)


if __name__ == "__main__":
    unittest.main()

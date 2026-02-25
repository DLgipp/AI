"""
Tests for Decision, Evolution, and Behavior modules.
"""

import unittest
from modules.decision.decision_layer import (
    DecisionLayer, DecisionVector, ResponseStrategy, EmotionalTone
)
from modules.evolution.evolution_layer import (
    EvolutionLayer, RewardSignal, RewardSource
)
from modules.behavior.behavior_processor import BehaviorProcessor


class TestDecisionLayer(unittest.TestCase):
    """Tests for DecisionLayer."""
    
    def setUp(self):
        self.layer = DecisionLayer()
    
    def test_decide_query_intent(self):
        """Test decision for query intent."""
        stance = {
            "verbosity": 0.6,
            "initiative": 0.5,
            "formality": 0.3,
            "confidence": 0.7,
            "engagement_level": 0.6,
            "dominant_trait": "curiosity",
            "emotion_tone": 0.3,
            "user_relationship": 0.5,
            "cognitive_conflicts": []
        }
        
        interpretation = {
            "intent": "query",
            "goal": {"goal_type": "informational", "priority": 0.7},
            "emotion_full": {"dominant_emotion": "neutral", "valence": 0.2},
            "importance": 0.6
        }
        
        decision = self.layer.decide(stance, interpretation, {})
        
        self.assertIn(decision.strategy, [
            ResponseStrategy.ANSWER_DIRECT,
            ResponseStrategy.ANSWER_DETAILED
        ])
    
    def test_decide_problem_intent(self):
        """Test decision for problem intent."""
        stance = {
            "verbosity": 0.5,
            "initiative": 0.5,
            "formality": 0.5,
            "confidence": 0.5,
            "engagement_level": 0.5,
            "dominant_trait": "empathy",
            "emotion_tone": -0.2,
            "user_relationship": 0.5,
            "cognitive_conflicts": []
        }
        
        interpretation = {
            "intent": "problem",
            "goal": {"goal_type": "task", "priority": 0.8},
            "emotion_full": {"dominant_emotion": "sadness", "valence": -0.5},
            "importance": 0.8
        }
        
        decision = self.layer.decide(stance, interpretation, {})
        
        self.assertEqual(decision.emotional_tone, EmotionalTone.EMPATHETIC)
        self.assertTrue(decision.include_empathy)
    
    def test_decide_high_engagement(self):
        """Test decision with high engagement."""
        stance = {
            "verbosity": 0.7,
            "initiative": 0.8,
            "formality": 0.3,
            "confidence": 0.8,
            "engagement_level": 0.9,
            "dominant_trait": "extraversion",
            "emotion_tone": 0.5,
            "user_relationship": 0.7,
            "cognitive_conflicts": []
        }
        
        interpretation = {
            "intent": "chat",
            "goal": {"goal_type": "social", "priority": 0.5},
            "emotion_full": {"dominant_emotion": "joy", "valence": 0.6},
            "importance": 0.5
        }
        
        decision = self.layer.decide(stance, interpretation, {})
        
        self.assertEqual(decision.strategy, ResponseStrategy.ENGAGE_SOCIAL)
        self.assertTrue(decision.include_questions)


class TestEvolutionLayer(unittest.TestCase):
    """Tests for EvolutionLayer."""
    
    def setUp(self):
        self.layer = EvolutionLayer()
    
    def test_calculate_reward_explicit_positive(self):
        """Test reward calculation with explicit positive feedback."""
        reward = self.layer.calculate_reward(
            user_reaction="Спасибо, очень помогло!",
            context={}
        )
        
        self.assertGreater(reward.value, 0.5)
        self.assertEqual(reward.source, RewardSource.USER_EXPLICIT)
    
    def test_calculate_reward_explicit_negative(self):
        """Test reward calculation with explicit negative feedback."""
        reward = self.layer.calculate_reward(
            user_reaction="Плохо, не помогло",
            context={}
        )
        
        self.assertLess(reward.value, -0.5)
    
    def test_calculate_reward_emotion_change(self):
        """Test reward calculation from emotion change."""
        reward = self.layer.calculate_reward(
            user_emotion_change=(0.5, 0.3),  # Positive valence change
            context={}
        )
        
        self.assertGreater(reward.value, 0)
    
    def test_calculate_reward_goal_achievement(self):
        """Test reward calculation from goal achievement."""
        reward = self.layer.calculate_reward(
            goal_achieved=True,
            context={}
        )
        
        self.assertGreater(reward.value, 0)
    
    def test_update_personality_positive(self):
        """Test personality update with positive rewards."""
        # Add enough reward history
        for _ in range(15):
            self.layer.calculate_reward(
                user_reaction="Отлично!",
                context={}
            )
        
        current_traits = {
            "assertiveness": 0.5,
            "curiosity": 0.5,
            "neuroticism": 0.5
        }
        current_values = {"helpfulness": 0.8}
        
        # Get latest reward
        reward = self.layer._reward_history[-1]
        
        updated_traits, updated_values, event = self.layer.update_personality(
            current_traits=current_traits,
            current_values=current_values,
            reward=reward
        )
        
        # With positive rewards, assertiveness should increase
        self.assertGreater(updated_traits["assertiveness"], 0.5)
    
    def test_get_learning_statistics(self):
        """Test learning statistics."""
        # Add some rewards
        for i in range(5):
            self.layer.calculate_reward(
                user_reaction="Хорошо" if i % 2 == 0 else "Плохо",
                context={}
            )
        
        stats = self.layer.get_learning_statistics()
        
        self.assertEqual(stats["total_rewards"], 5)
        self.assertIn("average_reward", stats)


class TestBehaviorProcessor(unittest.TestCase):
    """Tests for BehaviorProcessor."""
    
    def setUp(self):
        self.processor = BehaviorProcessor()
    
    def test_process_basic(self):
        """Test basic processing."""
        decision = DecisionVector(
            strategy=ResponseStrategy.ANSWER_DIRECT,
            emotional_tone=EmotionalTone.NEUTRAL,
            verbosity=0.5,
            initiative=0.5,
            formality=0.3
        )
        
        stance = {
            "dominant_trait": "neutral",
            "engagement_level": 0.5
        }
        
        output = self.processor.process(
            llm_output="Привет! Как дела?",
            decision=decision,
            stance=stance
        )
        
        self.assertIsInstance(output.text, str)
        self.assertGreater(len(output.text), 0)
    
    def test_process_length_constraint(self):
        """Test length constraint application."""
        decision = DecisionVector(
            strategy=ResponseStrategy.ANSWER_DETAILED,
            emotional_tone=EmotionalTone.NEUTRAL,
            verbosity=0.5,
            max_length=50
        )
        
        stance = {"dominant_trait": "neutral"}
        
        long_text = "Это очень длинный ответ, который определенно превышает лимит в пятьдесят символов и должен быть сокращен."
        
        output = self.processor.process(
            llm_output=long_text,
            decision=decision,
            stance=stance
        )
        
        self.assertLessEqual(len(output.text), 50 + 10)  # Some tolerance
    
    def test_process_empathy(self):
        """Test empathy inclusion."""
        decision = DecisionVector(
            strategy=ResponseStrategy.PROVIDE_SUPPORT,
            emotional_tone=EmotionalTone.EMPATHETIC,
            verbosity=0.5,
            include_empathy=True
        )
        
        stance = {"dominant_trait": "empathy"}
        
        output = self.processor.process(
            llm_output="Я понимаю вашу ситуацию.",
            decision=decision,
            stance=stance
        )
        
        # Empathy should be present
        self.assertTrue(output.style_adjustments.get("empathy_ensured", True))
    
    def test_cleanup_artifacts(self):
        """Test artifact cleanup."""
        decision = DecisionVector(
            strategy=ResponseStrategy.ANSWER_DIRECT,
            emotional_tone=EmotionalTone.NEUTRAL,
            verbosity=0.5
        )
        
        stance = {"dominant_trait": "neutral"}
        
        # Text with artifacts
        messy_text = "Привет   !!  Как   дела  ???"
        
        output = self.processor.process(
            llm_output=messy_text,
            decision=decision,
            stance=stance
        )
        
        # Should be cleaned up
        self.assertNotIn("   ", output.text)


if __name__ == "__main__":
    unittest.main()

"""
Tests for Interpretation Layer modules.
"""

import unittest
from modules.interpretation.topic_detector import TopicDetector, TopicResult
from modules.interpretation.goal_extractor import GoalExtractor, GoalResult
from modules.interpretation.importance_scorer import ImportanceScorer, ImportanceResult
from modules.interpretation import InterpretationLayer


class TestTopicDetector(unittest.TestCase):
    """Tests for TopicDetector."""
    
    def setUp(self):
        self.detector = TopicDetector()
    
    def test_detect_technology_topic(self):
        """Test technology topic detection."""
        result = self.detector.detect("Python программирование код разработка")
        
        self.assertEqual(result.category, "technology")
        self.assertIn(result.primary_topic, ["programming", "software", "ai_ml"])
    
    def test_detect_science_topic(self):
        """Test science topic detection."""
        result = self.detector.detect("Физика химия биология наука эксперимент")
        
        self.assertEqual(result.category, "science")
    
    def test_detect_entertainment_topic(self):
        """Test entertainment topic detection."""
        result = self.detector.detect("Фильм кино музыка игра сериал")
        
        self.assertEqual(result.category, "entertainment")
    
    def test_detect_emotions_topic(self):
        """Test emotions topic detection."""
        result = self.detector.detect("Чувства эмоции настроение переживания")
        
        self.assertEqual(result.category, "emotions")
    
    def test_topic_vector(self):
        """Test topic vector generation."""
        result = self.detector.detect("ИИ нейросеть машинное обучение")
        
        self.assertIsInstance(result.topic_vector, list)
        self.assertEqual(len(result.topic_vector), 5)
    
    def test_general_topic(self):
        """Test general topic for unclear input."""
        result = self.detector.detect("Бла бла бла")
        
        self.assertEqual(result.primary_topic, "general")


class TestGoalExtractor(unittest.TestCase):
    """Tests for GoalExtractor."""
    
    def setUp(self):
        self.extractor = GoalExtractor()
    
    def test_extract_informational_goal(self):
        """Test informational goal extraction."""
        result = self.extractor.extract("Хочу узнать больше про программирование")
        
        self.assertEqual(result.goal_type, "informational")
        self.assertIn("узнать", result.goal.lower() or "программирование" in result.goal.lower())
    
    def test_extract_task_goal(self):
        """Test task goal extraction."""
        result = self.extractor.extract("Сделай мне презентацию")
        
        self.assertEqual(result.goal_type, "task")
    
    def test_extract_creative_goal(self):
        """Test creative goal extraction."""
        result = self.extractor.extract("Придумай идею для проекта")
        
        self.assertEqual(result.goal_type, "creative")
    
    def test_extract_social_goal(self):
        """Test social goal extraction."""
        result = self.extractor.extract("Привет, давай поговорим")
        
        self.assertEqual(result.goal_type, "social")
    
    def test_extract_emotional_goal(self):
        """Test emotional goal extraction."""
        result = self.extractor.extract("Мне грустно, поддержи меня")
        
        self.assertEqual(result.goal_type, "emotional")
    
    def test_priority_calculation(self):
        """Test priority calculation."""
        result = self.extractor.extract("Очень важно срочно сделай")
        
        self.assertGreater(result.priority, 0.6)
    
    def test_urgency_calculation(self):
        """Test urgency calculation."""
        result = self.extractor.extract("Срочно! Немедленно!")
        
        self.assertGreater(result.urgency, 0.7)


class TestImportanceScorer(unittest.TestCase):
    """Tests for ImportanceScorer."""
    
    def setUp(self):
        self.scorer = ImportanceScorer()
    
    def test_calculate_importance_high_emotion(self):
        """Test high importance with high emotion."""
        result = self.scorer.calculate(
            text="Я в ярости!",
            emotion={"valence": -0.8, "arousal": 0.9, "anger": 0.9}
        )
        
        self.assertGreater(result.importance, 0.6)
    
    def test_calculate_importance_low_emotion(self):
        """Test lower importance with low emotion."""
        result = self.scorer.calculate(
            text="Обычный вопрос",
            emotion={"valence": 0.0, "arousal": 0.3, "neutral": 0.9}
        )
        
        self.assertLess(result.importance, 0.6)
    
    def test_calculate_importance_urgent_goal(self):
        """Test importance with urgent goal."""
        result = self.scorer.calculate(
            text="Нужно срочно",
            goal={"urgency": 0.9, "priority": 0.8}
        )
        
        self.assertGreater(result.importance, 0.6)
    
    def test_calculate_importance_important_topic(self):
        """Test importance with important topic."""
        result = self.scorer.calculate(
            text="Вопрос о здоровье",
            topic={"primary_topic": "health", "category": "lifestyle"}
        )
        
        self.assertGreater(result.importance, 0.6)
    
    def test_factors_present(self):
        """Test that all factors are calculated."""
        result = self.scorer.calculate("Тестовый текст")
        
        self.assertIn("emotion_intensity", result.factors)
        self.assertIn("urgency", result.factors)
        self.assertIn("goal_priority", result.factors)
        self.assertIn("topic_relevance", result.factors)


class TestInterpretationLayer(unittest.TestCase):
    """Tests for unified InterpretationLayer."""
    
    def setUp(self):
        self.layer = InterpretationLayer()
    
    def test_process_basic(self):
        """Test basic interpretation."""
        result = self.layer.process(
            text="Расскажи про искусственный интеллект",
            perception={
                "emotion": {"valence": 0.3, "arousal": 0.5},
                "intent": {"intent": "query"}
            }
        )
        
        self.assertIn("intent", result)
        self.assertIn("topic", result)
        self.assertIn("goal", result)
        self.assertIn("importance", result)
    
    def test_process_complete(self):
        """Test complete interpretation pipeline."""
        result = self.layer.process(
            text="Срочно помоги с проблемой, очень важно!",
            perception={
                "emotion": {"valence": -0.5, "arousal": 0.8, "anger": 0.6},
                "intent": {"intent": "problem"}
            },
            context={"ongoing_task": True}
        )
        
        self.assertGreater(result["importance"], 0.6)
        self.assertEqual(result["goal"]["goal_type"], "task")


if __name__ == "__main__":
    unittest.main()

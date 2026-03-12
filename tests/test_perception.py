"""
Tests for Perception Layer modules.
"""

import unittest
from modules.perception.input_normalizer import InputNormalizer, PerceivedInput
from modules.perception.emotion_detector import EmotionDetector, EmotionState
from modules.perception.intent_detector import IntentDetector, IntentResult
from modules.perception import PerceptionLayer


class TestInputNormalizer(unittest.TestCase):
    """Tests for InputNormalizer."""
    
    def setUp(self):
        self.normalizer = InputNormalizer()
    
    def test_normalize_basic(self):
        """Test basic normalization."""
        result = self.normalizer.normalize("Привет, как дела?")
        
        self.assertEqual(result.text, "Привет, как дела?")
        self.assertEqual(result.speaker, "user")
        self.assertIsNotNone(result.timestamp)
    
    def test_normalize_cleans_text(self):
        """Test text cleaning."""
        result = self.normalizer.normalize("  Ммм  ,   привет  ")
        
        self.assertNotIn("  ", result.text)  # No double spaces
        self.assertEqual(result.text.strip(), result.text)
    
    def test_normalize_with_context(self):
        """Test with additional context."""
        result = self.normalizer.normalize(
            "Текст",
            speaker="test_user",
            silence_duration=10.5,
            interruption=True
        )
        
        self.assertEqual(result.speaker, "test_user")
        self.assertEqual(result.silence_duration, 10.5)
        self.assertTrue(result.interruption)


class TestEmotionDetector(unittest.TestCase):
    """Tests for EmotionDetector."""
    
    def setUp(self):
        self.detector = EmotionDetector()
    
    def test_detect_positive_emotion(self):
        """Test positive emotion detection."""
        result = self.detector.detect("Отлично! Я очень рад!")
        
        self.assertGreater(result.valence, 0)
        self.assertGreater(result.joy, 0.3)
    
    def test_detect_negative_emotion(self):
        """Test negative emotion detection."""
        result = self.detector.detect("Плохо, мне грустно и тоскливо")
        
        self.assertLess(result.valence, 0)
        self.assertGreater(result.sadness, 0.3)
    
    def test_detect_anger(self):
        """Test anger detection."""
        result = self.detector.detect("Я злюсь, это бесит!")
        
        self.assertGreater(result.anger, 0.5)
    
    def test_detect_fear(self):
        """Test fear detection."""
        result = self.detector.detect("Боюсь, это страшно")
        
        self.assertGreater(result.fear, 0.5)
    
    def test_detect_surprise(self):
        """Test surprise detection."""
        result = self.detector.detect("Вау! Ого! Неожиданно!")
        
        self.assertGreater(result.surprise, 0.5)
    
    def test_neutral_emotion(self):
        """Test neutral emotion."""
        result = self.detector.detect("Обычный день, ничего особенного")
        
        self.assertGreater(result.neutral, 0.5)
    
    def test_dominant_emotion(self):
        """Test dominant emotion identification."""
        result = self.detector.detect("Я очень счастлив и рад!")
        
        self.assertEqual(result.dominant_emotion, "joy")


class TestIntentDetector(unittest.TestCase):
    """Tests for IntentDetector."""
    
    def setUp(self):
        self.detector = IntentDetector()
    
    def test_detect_query_intent(self):
        """Test query intent detection."""
        result = self.detector.detect("Что такое искусственный интеллект?")
        
        self.assertEqual(result.intent, "query")
        self.assertGreater(result.confidence, 0.5)
    
    def test_detect_request_intent(self):
        """Test request intent detection."""
        result = self.detector.detect("Сделай мне кофе, пожалуйста")
        
        self.assertEqual(result.intent, "request")
    
    def test_detect_chat_intent(self):
        """Test chat intent detection."""
        result = self.detector.detect("Привет! Как дела?")
        
        self.assertEqual(result.intent, "chat")
    
    def test_detect_creative_intent(self):
        """Test creative intent detection."""
        result = self.detector.detect("Придумай что-нибудь интересное")
        
        self.assertEqual(result.intent, "creative")
    
    def test_detect_problem_intent(self):
        """Test problem intent detection."""
        result = self.detector.detect("У меня не работает программа")
        
        self.assertEqual(result.intent, "problem")
    
    def test_unknown_intent(self):
        """Test unknown intent handling."""
        result = self.detector.detect("Абырвалг шарыг рым")
        
        self.assertEqual(result.intent, "unknown")


class TestPerceptionLayer(unittest.TestCase):
    """Tests for unified PerceptionLayer."""
    
    def setUp(self):
        self.layer = PerceptionLayer()
    
    def test_process_basic(self):
        """Test basic processing."""
        result = self.layer.process("Привет, расскажи про ИИ")
        
        self.assertIn("perceived_input", result)
        self.assertIn("emotion", result)
        self.assertIn("intent", result)
    
    def test_process_complete(self):
        """Test processing with all parameters."""
        result = self.layer.process(
            text="Вау! Это невероятно!",
            voice_features={"energy": 0.8, "pitch": 0.7},
            silence_duration=5.0,
            interruption=False
        )
        
        self.assertEqual(result["perceived_input"]["text"], "Вау! Это невероятно!")
        self.assertGreater(result["emotion"]["joy"], 0.3)
        self.assertIn(result["intent"]["intent"], ["chat", "creative", "opinion"])


if __name__ == "__main__":
    unittest.main()

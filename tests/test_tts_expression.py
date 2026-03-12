"""
Unit tests for TTS Expression and SSML generation.

Tests cover:
- is_last_sentence() function
- SSML validation
- SSML repair
- SSML stripping
- Full convert_to_ssml() pipeline
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.tts.tts_expression import (
    is_last_sentence,
    validate_ssml,
    repair_ssml,
    strip_ssml,
    convert_to_ssml,
    TTSExpressionProcessor,
    ExpressionContext
)


class TestIsLastSentence(unittest.TestCase):
    """Tests for is_last_sentence() function."""

    def test_ends_with_period(self):
        """Sentence ending with period should be last."""
        self.assertTrue(is_last_sentence("Hello world."))
        self.assertTrue(is_last_sentence("Привет мир."))

    def test_ends_with_exclamation(self):
        """Sentence ending with exclamation should be last."""
        self.assertTrue(is_last_sentence("Hello!"))
        self.assertTrue(is_last_sentence("Привет!"))

    def test_ends_with_question(self):
        """Sentence ending with question mark should be last."""
        self.assertTrue(is_last_sentence("How are you?"))
        self.assertTrue(is_last_sentence("Как дела?"))

    def test_ends_with_ellipsis(self):
        """Sentence ending with ellipsis should be last."""
        self.assertTrue(is_last_sentence("Hmm..."))
        self.assertTrue(is_last_sentence("Ну что ж…"))

    def test_no_terminal_punctuation(self):
        """Sentence without terminal punctuation is not last."""
        self.assertFalse(is_last_sentence("Hello world"))
        self.assertFalse(is_last_sentence("Привет мир"))

    def test_ends_with_comma(self):
        """Sentence ending with comma is not last."""
        self.assertFalse(is_last_sentence("Hello world,"))
        self.assertFalse(is_last_sentence("Привет мир,"))

    def test_empty_string(self):
        """Empty string should not be last."""
        self.assertFalse(is_last_sentence(""))
        self.assertFalse(is_last_sentence("   "))

    def test_with_trailing_quotes(self):
        """Should handle trailing quotes correctly."""
        self.assertTrue(is_last_sentence("Hello world.\""))
        self.assertTrue(is_last_sentence("Привет.'"))


class TestValidateSSML(unittest.TestCase):
    """Tests for validate_ssml() function."""

    def test_valid_ssml(self):
        """Valid SSML should pass validation."""
        ssml = """<speak>
            <p>
                <s><prosody rate="medium">Hello</prosody></s>
            </p>
        </speak>"""
        is_valid, error = validate_ssml(ssml)
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_missing_speak_tag(self):
        """Missing speak tag should fail."""
        ssml = "<p>Hello</p>"
        is_valid, error = validate_ssml(ssml)
        self.assertFalse(is_valid)
        self.assertIn("speak", error)

    def test_empty_string(self):
        """Empty string should fail."""
        is_valid, error = validate_ssml("")
        self.assertFalse(is_valid)
        self.assertIn("Empty", error)

    def test_malformed_xml(self):
        """Malformed XML should fail."""
        ssml = "<speak><p>Hello</speak>"
        is_valid, error = validate_ssml(ssml)
        self.assertFalse(is_valid)
        self.assertIn("parse error", error.lower())


class TestRepairSSML(unittest.TestCase):
    """Tests for repair_ssml() function."""

    def test_add_missing_speak(self):
        """Should add missing speak tags."""
        ssml = "<p>Hello</p>"
        repaired = repair_ssml(ssml)
        self.assertIn("<speak>", repaired)
        self.assertIn("</speak>", repaired)

    def test_self_closing_break(self):
        """Should convert break to self-closing."""
        ssml = "<speak><break time=\"100ms\"></speak>"
        repaired = repair_ssml(ssml)
        self.assertIn("<break", repaired)

    def test_empty_string(self):
        """Empty string should remain empty."""
        self.assertEqual(repair_ssml(""), "")


class TestStripSSML(unittest.TestCase):
    """Tests for strip_ssml() function."""

    def test_strip_prosody(self):
        """Should remove prosody tags."""
        ssml = '<speak><prosody rate="fast">Hello</prosody></speak>'
        plain = strip_ssml(ssml)
        self.assertEqual(plain, "Hello")

    def test_strip_all_tags(self):
        """Should remove all SSML tags."""
        ssml = """<speak>
            <p>
                <s><prosody rate="medium">Hello World</prosody></s>
            </p>
        </speak>"""
        plain = strip_ssml(ssml)
        self.assertEqual(plain, "Hello World")

    def test_cleanup_whitespace(self):
        """Should clean up extra whitespace."""
        ssml = "<speak>   Hello    World   </speak>"
        plain = strip_ssml(ssml)
        self.assertEqual(plain, "Hello World")

    def test_empty_string(self):
        """Empty string should remain empty."""
        self.assertEqual(strip_ssml(""), "")


class TestConvertToSSML(unittest.TestCase):
    """Tests for convert_to_ssml() function."""

    def test_basic_conversion(self):
        """Basic text should convert to valid SSML."""
        ssml = convert_to_ssml("Привет! Как дела?")
        is_valid, error = validate_ssml(ssml)
        self.assertTrue(is_valid, f"SSML invalid: {error}")
        self.assertIn("<speak>", ssml)
        self.assertIn("</speak>", ssml)

    def test_with_emotion(self):
        """Should handle emotion parameter."""
        ssml = convert_to_ssml(
            "Это замечательно!",
            emotion={"joy": 0.8}
        )
        is_valid, error = validate_ssml(ssml)
        self.assertTrue(is_valid, f"SSML invalid: {error}")

    def test_with_context(self):
        """Should handle full context."""
        ssml = convert_to_ssml(
            "Давайте разберёмся.",
            emotion={"curiosity": 0.6},
            emotional_tone="WARM",
            decision_strategy="EXPLAIN",
            dominant_trait="empathy",
            engagement_level=0.7
        )
        is_valid, error = validate_ssml(ssml)
        self.assertTrue(is_valid, f"SSML invalid: {error}")

    def test_fallback_on_invalid(self):
        """Should return plain text if validation fails and repair disabled."""
        # This tests the fallback mechanism
        ssml = convert_to_ssml(
            "Test text.",
            validate=False  # Skip validation for this test
        )
        # Should still produce SSML structure
        self.assertIn("<speak>", ssml)

    def test_multiple_sentences(self):
        """Should handle multiple sentences."""
        ssml = convert_to_ssml("Первое предложение. Второе предложение? Третье!")
        is_valid, error = validate_ssml(ssml)
        self.assertTrue(is_valid, f"SSML invalid: {error}")
        
        # Should contain multiple <s> tags
        self.assertTrue(ssml.count("<s>") >= 2)


class TestTTSExpressionProcessor(unittest.TestCase):
    """Tests for TTSExpressionProcessor class."""

    def setUp(self):
        """Set up test fixtures."""
        self.processor = TTSExpressionProcessor()

    def test_get_primary_emotion_none(self):
        """Should return neutral when no emotion."""
        emotion = self.processor._get_primary_emotion(None)
        self.assertEqual(emotion, "neutral")

    def test_get_primary_emotion_empty(self):
        """Should return neutral for empty emotion dict."""
        emotion = self.processor._get_primary_emotion({})
        self.assertEqual(emotion, "neutral")

    def test_get_primary_emotion_dominant(self):
        """Should return emotion with highest value."""
        emotion = self.processor._get_primary_emotion({
            "joy": 0.3,
            "sadness": 0.8,
            "anger": 0.5
        })
        self.assertEqual(emotion, "sadness")

    def test_get_primary_emotion_below_threshold(self):
        """Should return neutral if all emotions below threshold."""
        emotion = self.processor._get_primary_emotion({
            "joy": 0.1,
            "sadness": 0.2
        })
        self.assertEqual(emotion, "neutral")

    def test_split_sentences(self):
        """Should split text into sentences."""
        sentences = self.processor._split_sentences("Первое. Второе! Третье?")
        self.assertEqual(len(sentences), 3)
        self.assertEqual(sentences[0], "Первое.")
        self.assertEqual(sentences[1], "Второе!")
        self.assertEqual(sentences[2], "Третье?")

    def test_process_with_context(self):
        """Should process text with full context."""
        context = ExpressionContext(
            emotion={"joy": 0.7},
            emotional_tone="ENTHUSIASTIC",
            decision_strategy="ENGAGE_SOCIAL",
            dominant_trait="extraversion",
            engagement_level=0.8
        )
        result = self.processor.process("Привет! Как твои дела?", context)
        
        # Should be valid SSML
        is_valid, error = validate_ssml(result)
        self.assertTrue(is_valid, f"SSML invalid: {error}")


class TestIntegration(unittest.TestCase):
    """Integration tests for full pipeline."""

    def test_full_pipeline_joy(self):
        """Full pipeline with joy emotion."""
        text = "Это отличная новость!"
        ssml = convert_to_ssml(
            text=text,
            emotion={"joy": 0.8},
            emotional_tone="ENTHUSIASTIC",
            decision_strategy="ENGAGE_SOCIAL",
            dominant_trait="extraversion",
            engagement_level=0.9
        )
        
        # Validate structure
        is_valid, error = validate_ssml(ssml)
        self.assertTrue(is_valid, f"SSML invalid: {error}")
        
        # Should contain prosody
        self.assertIn("prosody", ssml)
        
        # Should be able to strip back to original
        plain = strip_ssml(ssml)
        self.assertIn("новость", plain)

    def test_full_pipeline_sadness(self):
        """Full pipeline with sadness emotion."""
        text = "Мне жаль это слышать."
        ssml = convert_to_ssml(
            text=text,
            emotion={"sadness": 0.7},
            emotional_tone="EMPATHETIC",
            decision_strategy="PROVIDE_SUPPORT",
            dominant_trait="empathy",
            engagement_level=0.5
        )
        
        # Validate structure
        is_valid, error = validate_ssml(ssml)
        self.assertTrue(is_valid, f"SSML invalid: {error}")

    def test_full_pipeline_neutral(self):
        """Full pipeline with neutral emotion."""
        text = "Средняя температура по больнице."
        ssml = convert_to_ssml(
            text=text,
            emotion=None,
            emotional_tone="NEUTRAL",
            decision_strategy="ANSWER_DIRECT",
            dominant_trait="neutral",
            engagement_level=0.5
        )
        
        # Validate structure
        is_valid, error = validate_ssml(ssml)
        self.assertTrue(is_valid, f"SSML invalid: {error}")


if __name__ == "__main__":
    unittest.main()

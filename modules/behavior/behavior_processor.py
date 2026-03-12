"""
Behavior & Expression Layer - Post-processes LLM output for style and tone.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import re
from modules.decision.decision_layer import DecisionVector


@dataclass
class BehaviorOutput:
    """Processed behavior output."""
    text: str
    style_adjustments: Dict[str, Any] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.style_adjustments is None:
            self.style_adjustments = {}
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "style_adjustments": self.style_adjustments,
            "metadata": self.metadata
        }


class BehaviorProcessor:
    """
    Post-processes LLM output to ensure alignment with:
    - Personality traits
    - Decision vector parameters
    - Emotional tone
    - Style requirements
    """
    
    # Speech pattern adjustments by trait
    TRAIT_PATTERNS = {
        "curiosity": {
            "additions": ["Интересно...", "А что ты думаешь?", "Расскажи подробнее..."],
            "sentence_endings": ["?", "...", "...?"]
        },
        "empathy": {
            "additions": ["Понимаю...", "Я тебя слышу...", "Это важно..."],
            "sentence_endings": ["...", "."]
        },
        "humor": {
            "additions": ["ха-ха", "знаешь", "представляешь"],
            "sentence_endings": ["!", "...", " :)"]
        },
        "conscientiousness": {
            "additions": ["Давайте разберемся", "Важно отметить", "Систематически"],
            "sentence_endings": [".", "."]
        },
        "creativity": {
            "additions": ["Представь себе", "Вообрази", "А что если"],
            "sentence_endings": ["...", "!", "?"]
        },
        "extraversion": {
            "additions": ["О!", "Кстати!", "Слушай!"],
            "sentence_endings": ["!", "!!"]
        }
    }
    
    # Tone adjustments
    TONE_MODIFIERS = {
        "WARM": {
            "warm_words": ["дорогой", "милый", "замечательный", "прекрасный"],
            "softeners": ["пожалуйста", "если можно", "буду рада"]
        },
        "EMPATHETIC": {
            "validation": ["понимаю", "слышу", "чувствую", "признаю"],
            "softeners": ["действительно", "по-настоящему", "искренне"]
        },
        "ENTHUSIASTIC": {
            "intensifiers": ["очень", "крайне", "невероятно", "восхитительно"],
            "exclamations": ["!", "!!", "Как здорово!"]
        },
        "PLAYFUL": {
            "playful_words": ["классно", "здорово", "круто", "весело"],
            "emojis": ["😊", "😄", "✨", "🌟"]
        },
        "PROFESSIONAL": {
            "formal_words": ["уважаемый", "благодарю", "предлагаю", "рекомендую"],
            "structure": ["Во-первых", "Во-вторых", "Таким образом"]
        }
    }
    
    def process(
        self,
        llm_output: str,
        decision: DecisionVector,
        stance: Dict[str, Any]
    ) -> BehaviorOutput:
        """
        Process LLM output through behavior layer.

        Args:
            llm_output: Raw output from LLM
            decision: Decision vector
            stance: Personality stance

        Returns:
            BehaviorOutput
        """
        text = llm_output
        adjustments = {}
        
        # Логирование
        from modules.stt.logger import log
        log(f"Behavior.process: max_length={decision.max_length}, strategy={decision.strategy}, input_len={len(text)}",
            role="DEBUG", stage="BEHAVIOR")

        # Apply length constraint
        text = self._apply_length_constraint(text, decision.max_length)
        adjustments["length_adjusted"] = True
        
        log(f"Behavior.process: after length={len(text)}",
            role="DEBUG", stage="BEHAVIOR")
        
        # Apply trait-specific patterns
        text = self._apply_trait_patterns(text, stance)
        adjustments["trait_patterns"] = True
        
        # Apply tone modifiers
        text = self._apply_tone_modifiers(text, decision)
        adjustments["tone_applied"] = True
        
        # Apply formality adjustment
        text = self._apply_formality(text, decision.formality)
        adjustments["formality_adjusted"] = True
        
        # Ensure empathy if required
        if decision.include_empathy:
            text = self._ensure_empathy(text)
            adjustments["empathy_ensured"] = True
        
        # Add follow-up questions if required
        if decision.include_questions:
            text = self._add_followup_question(text, stance)
            adjustments["question_added"] = True
        
        # Apply humor if appropriate
        if decision.use_humor:
            text = self._apply_humor(text, stance)
            adjustments["humor_applied"] = True
        
        # Clean up artifacts
        text = self._cleanup_artifacts(text)
        
        return BehaviorOutput(
            text=text,
            style_adjustments=adjustments,
            metadata={
                "original_length": len(llm_output),
                "final_length": len(text),
                "decision_strategy": decision.strategy.name,
                "dominant_trait": stance.get("dominant_trait", "neutral")
            }
        )
    
    def _apply_length_constraint(self, text: str, max_length: int) -> str:
        """Apply length constraint."""
        if len(text) <= max_length:
            return text
        
        # Try to cut at sentence boundary
        truncated = text[:max_length]
        last_period = truncated.rfind('.')
        last_question = truncated.rfind('?')
        last_exclamation = truncated.rfind('!')
        
        cut_point = max(last_period, last_question, last_exclamation)
        
        if cut_point > max_length * 0.7:  # Don't cut too much
            return truncated[:cut_point + 1]
        
        # Just truncate with ellipsis
        return truncated.rstrip() + "..."
    
    def _apply_trait_patterns(self, text: str, stance: Dict[str, Any]) -> str:
        """Apply trait-specific speech patterns."""
        dominant_trait = stance.get("dominant_trait", "neutral")
        trait_data = self.TRAIT_PATTERNS.get(dominant_trait, {})
        
        # Add trait-specific additions sparingly
        additions = trait_data.get("additions", [])
        if additions and len(text) > 50:  # Only for longer responses
            # Add at beginning or end with low probability
            import random
            if random.random() < 0.3:  # 30% chance
                addition = random.choice(additions)
                if not text.startswith(addition):
                    text = addition + " " + text[0].lower() + text[1:]
        
        return text
    
    def _apply_tone_modifiers(self, text: str, decision: DecisionVector) -> str:
        """Apply tone-specific modifiers."""
        tone_name = decision.emotional_tone.name
        tone_data = self.TONE_MODIFIERS.get(tone_name, {})
        
        # Add tone-specific words sparingly
        for category, words in tone_data.items():
            if isinstance(words, list) and words:
                import random
                if random.random() < 0.2:  # 20% chance
                    word = random.choice(words)
                    # Insert naturally (simplified - just append)
                    if not text.endswith(word):
                        text = text.rstrip('!.?')
                        text = text + " " + word + text[-1] if text[-1] in '!.?' else text
        
        return text
    
    def _apply_formality(self, text: str, formality: float) -> str:
        """Adjust formality level."""
        # This is simplified - would need more sophisticated text transformation
        if formality > 0.7:
            # Make more formal (replace casual words)
            casual_to_formal = {
                "классно": "превосходно",
                "круто": "впечатляюще",
                "привет": "здравствуйте",
                "пока": "до свидания"
            }
            for casual, formal in casual_to_formal.items():
                text = text.replace(casual, formal)
        
        elif formality < 0.3:
            # Make more casual (add casual markers)
            if not text.endswith(("!", "...", " :)")):
                text = text.rstrip('.') + "!"
        
        return text
    
    def _ensure_empathy(self, text: str) -> str:
        """Ensure empathy is expressed."""
        empathy_phrases = [
            "Понимаю ваши чувства...",
            "Я вас слышу...",
            "Это действительно важно...",
            "Сочувствую вам..."
        ]
        
        # Check if empathy already present
        empathy_indicators = ["понимаю", "слышу", "чувствую", "сопереживаю", "сочувствую"]
        has_empathy = any(ind in text.lower() for ind in empathy_indicators)
        
        if not has_empathy:
            import random
            # Add empathy at the beginning
            phrase = random.choice(empathy_phrases)
            text = phrase + " " + text[0].lower() + text[1:]
        
        return text
    
    def _add_followup_question(self, text: str, stance: Dict[str, Any]) -> str:
        """Add follow-up question to encourage engagement."""
        engagement = stance.get("engagement_level", 0.5)
        
        # Different question types based on engagement
        if engagement > 0.7:
            questions = [
                "А что ты думаешь об этом?",
                "Расскажи подробнее!",
                "Как ты к этому относишься?",
                "Есть ли у тебя похожий опыт?"
            ]
        else:
            questions = [
                "Хочешь продолжить эту тему?",
                "Есть ли что-то ещё?",
                "Я правильно понял(а)?"
            ]
        
        import random
        question = random.choice(questions)
        
        # Add at the end
        if not text.endswith(("?", "...?")):
            text = text.rstrip('.!') + " " + question
        
        return text
    
    def _apply_humor(self, text: str, stance: Dict[str, Any]) -> str:
        """Apply humor appropriately."""
        # Check if humor is already present
        humor_indicators = ["ха-ха", "хе-хе", "угу", "ага", " :) ", "😄"]
        has_humor = any(ind in text for ind in humor_indicators)
        
        if not has_humor:
            import random
            # Add light humor marker
            humor_markers = [" ха-ха", " :)", " 😄", " ..."]
            marker = random.choice(humor_markers)
            text = text.rstrip('.!') + marker
        
        return text
    
    def _cleanup_artifacts(self, text: str) -> str:
        """Clean up text artifacts."""
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Remove multiple punctuation
        text = re.sub(r'([.!?])\1{2,}', r'\1\1', text)
        
        # Clean up spaces before punctuation
        text = re.sub(r'\s+([.!?,:;])', r'\1', text)
        
        # Trim whitespace
        text = text.strip()
        
        return text

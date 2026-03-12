"""
Intent Detection Module - Detects user intent from input.
"""

from dataclasses import dataclass
from typing import Dict, Optional, List, Set
import re


@dataclass
class IntentResult:
    """Detected intent with confidence and metadata."""
    intent: str
    confidence: float = 1.0
    sub_intent: Optional[str] = None
    entities: Dict[str, str] = None
    raw_score: float = 0.0
    
    def __post_init__(self):
        if self.entities is None:
            self.entities = {}
    
    def to_dict(self) -> Dict[str, any]:
        return {
            "intent": self.intent,
            "confidence": self.confidence,
            "sub_intent": self.sub_intent,
            "entities": self.entities,
            "raw_score": self.raw_score
        }


class IntentDetector:
    """
    Rule-based intent detector (can be extended with ML models).
    """
    
    # Intent categories
    INTENTS = {
        # Information seeking
        "query": {
            "patterns": [
                r"что\s+(такое|значит|это)",
                r"как\s+(работает|сделать|узнать)",
                r"почему\s+",
                r"где\s+(найти|можно|взять)",
                r"когда\s+",
                r"кто\s+(такой|это)",
                r"расскажи\s+(про|о|мне)",
                r"объясни\s+",
                r"что ты знаешь",
                r"какой\s+",
                r"какая\s+",
                r"какие\s+"
            ],
            "keywords": {"что", "как", "почему", "где", "когда", "кто", "расскажи", "объясни"}
        },
        
        # Task request
        "request": {
            "patterns": [
                r"сделай\s+",
                r"помоги\s+",
                r"найди\s+",
                r"покажи\s+",
                r"открой\s+",
                r"запусти\s+",
                r"создай\s+",
                r"напиши\s+",
                r"давай\s+",
                r"нужно\s+чтобы",
                r"хочу\s+чтобы"
            ],
            "keywords": {"сделай", "помоги", "найди", "покажи", "открой", "запусти", "создай"}
        },
        
        # Conversation / chat
        "chat": {
            "patterns": [
                r"привет\s*!?",
                r"здравствуй\s*!?",
                r"добрый\s+(день|утро|вечер)",
                r"как\s+(дела|жизнь|настроение)",
                r"что\s+нового",
                r"пока\s*!?",
                r"до\s+свидания",
                r"спасибо\s*!?",
                r"благодарю\s*!?",
                r"ты\s+(кто|как|зачем)"
            ],
            "keywords": {"привет", "здравствуй", "пока", "спасибо", "благодарю", "дела"}
        },
        
        # Opinion / advice seeking
        "opinion": {
            "patterns": [
                r"что\s+ты\s+думаешь",
                r"как\s+ты\s+считаешь",
                r"твое\s+мнение",
                r"стоит\s+ли",
                r"лучше\s+",
                r"какой\s+выбор",
                r"посоветуй\s+",
                r"что\s+лучше"
            ],
            "keywords": {"думаешь", "считаешь", "мнение", "стоит", "лучше", "посоветуй"}
        },
        
        # Creative request
        "creative": {
            "patterns": [
                r"придумай\s+",
                r"напиши\s+(стих|песню|историю|сказку)",
                r"сочини\s+",
                r"сгенерируй\s+",
                r"создай\s+(образ|текст|идею)",
                r"предложи\s+(идею|вариант)"
            ],
            "keywords": {"придумай", "сочини", "сгенерируй", "идею", "творческий"}
        },
        
        # Problem / complaint
        "problem": {
            "patterns": [
                r"не\s+работает",
                r"сломалось",
                r"ошибка\s+",
                r"проблема\s+",
                r"не\s+получается",
                r"не\s+могу\s+",
                r"что-то\s+не\s+так"
            ],
            "keywords": {"не работает", "сломалось", "ошибка", "проблема", "не получается"}
        },
        
        # Confirmation / yes-no
        "confirmation": {
            "patterns": [
                r"да\s*!?",
                r"нет\s*!?",
                r"конечно\s*!?",
                r"верно\s*!?",
                r"правильно\s*!?",
                r"точно\s*!?",
                r"ага\s*!?",
                r"угу\s*!?"
            ],
            "keywords": {"да", "нет", "конечно", "верно", "правильно", "точно"}
        },
        
        # Memory / recall
        "recall": {
            "patterns": [
                r"помнишь\s+",
                r"ты\s+помнишь",
                r"вспоминаешь\s+",
                r"что\s+было\s+",
                r"раньше\s+ты\s+",
                r"мы\s+(обсуждали|говорили)"
            ],
            "keywords": {"помнишь", "вспоминаешь", "было", "раньше", "обсуждали"}
        },
        
        # Silence / filler
        "filler": {
            "patterns": [
                r"ммм\s*",
                r"эээ\s*",
                r"ну\s*",
                r"так\s*",
                r"ладно\s*",
                r"хорошо\s*"
            ],
            "keywords": {"ммм", "эээ", "ну", "так"}
        }
    }
    
    def detect(self, text: str) -> IntentResult:
        """
        Detect intent from text.
        
        Args:
            text: Input text
            
        Returns:
            IntentResult with detected intent and metadata
        """
        text_lower = text.lower().strip()
        words = set(re.findall(r'\w+', text_lower))
        
        best_intent = "unknown"
        best_score = 0.0
        best_sub_intent = None
        entities = {}
        
        for intent_name, intent_data in self.INTENTS.items():
            patterns = intent_data["patterns"]
            keywords = intent_data["keywords"]
            
            # Pattern matching score
            pattern_score = self._match_patterns(text_lower, patterns)
            
            # Keyword matching score
            keyword_score = self._match_keywords(words, keywords)
            
            # Combined score (patterns weighted higher)
            combined_score = pattern_score * 0.7 + keyword_score * 0.3
            
            if combined_score > best_score:
                best_score = combined_score
                best_intent = intent_name
                
                # Extract sub-intent from matched pattern
                matched_pattern = self._find_matched_pattern(text_lower, patterns)
                if matched_pattern:
                    best_sub_intent = matched_pattern
            
            # Extract entities
            intent_entities = self._extract_entities(text, intent_name)
            entities.update(intent_entities)
        
        # Apply threshold
        confidence = min(1.0, best_score) if best_score > 0.3 else max(0.0, best_score)
        
        # If score too low, mark as unknown
        if best_score < 0.2:
            best_intent = "unknown"
            confidence = 0.3
        
        return IntentResult(
            intent=best_intent,
            confidence=confidence,
            sub_intent=best_sub_intent,
            entities=entities,
            raw_score=best_score
        )
    
    def _match_patterns(self, text: str, patterns: List[str]) -> float:
        """Match text against regex patterns."""
        for pattern in patterns:
            if re.search(pattern, text):
                return 1.0
        return 0.0
    
    def _match_keywords(self, words: Set[str], keywords: Set[str]) -> float:
        """Match words against keyword set."""
        matches = len(words & keywords)
        if matches == 0:
            return 0.0
        elif matches == 1:
            return 0.5
        elif matches == 2:
            return 0.75
        else:
            return 1.0
    
    def _find_matched_pattern(self, text: str, patterns: List[str]) -> Optional[str]:
        """Find which pattern matched."""
        for pattern in patterns:
            if re.search(pattern, text):
                return pattern
        return None
    
    def _extract_entities(self, text: str, intent: str) -> Dict[str, str]:
        """Extract entities from text based on intent."""
        entities = {}
        
        # Time entities
        time_patterns = [
            (r"сегодня", "today"),
            (r"завтра", "tomorrow"),
            (r"вчера", "yesterday"),
            (r"утром", "morning"),
            (r"вечером", "evening"),
            (r"ночью", "night"),
            (r"днем", "afternoon")
        ]
        
        for pattern, value in time_patterns:
            if pattern in text.lower():
                entities["time"] = value
                break
        
        # Topic entities (simplified - words after key phrases)
        if intent in ["query", "request", "creative"]:
            # Extract potential topic (last significant word)
            words = re.findall(r'\w{4,}', text.lower())
            if words and len(words) > 1:
                entities["topic"] = words[-1]
        
        return entities

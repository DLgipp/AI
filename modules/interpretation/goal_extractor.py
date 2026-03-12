"""
Goal Extraction Module - Extracts user goals from input.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
import re


@dataclass
class GoalResult:
    """Extracted goal with metadata."""
    goal: str
    goal_type: str = "unknown"  # informational, task, creative, social, emotional
    confidence: float = 1.0
    subgoals: List[str] = field(default_factory=list)
    required_actions: List[str] = field(default_factory=list)
    priority: float = 0.5  # 0.0 (low) to 1.0 (high)
    urgency: float = 0.5  # 0.0 (low) to 1.0 (high)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal": self.goal,
            "goal_type": self.goal_type,
            "confidence": self.confidence,
            "subgoals": self.subgoals,
            "required_actions": self.required_actions,
            "priority": self.priority,
            "urgency": self.urgency
        }


class GoalExtractor:
    """
    Extracts user goals from input text.
    """
    
    # Goal type patterns
    GOAL_PATTERNS = {
        "informational": {
            "patterns": [
                r"узнать\s+",
                r"понять\s+",
                r"разобраться\s+",
                r"найти\s+информацию",
                r"что\s+(такое|значит)",
                r"как\s+(работает|устроить)",
                r"почему\s+",
                r"расскажи\s+",
                r"объясни\s+"
            ],
            "keywords": {"узнать", "понять", "разобраться", "информация", "объясни"}
        },
        "task": {
            "patterns": [
                r"сделай\s+",
                r"выполни\s+",
                r"помоги\s+сделать",
                r"нужно\s+",
                r"требуется\s+",
                r"задача\s+",
                r"хочу\s+чтобы\s+",
                r"давай\s+"
            ],
            "keywords": {"сделай", "выполни", "помоги", "нужно", "задача", "требуется"}
        },
        "creative": {
            "patterns": [
                r"придумай\s+",
                r"создай\s+",
                r"сгенерируй\s+",
                r"напиши\s+(стих|текст|песню)",
                r"сочини\s+",
                r"предложи\s+(идею|вариант)"
            ],
            "keywords": {"придумай", "создай", "сгенерируй", "идея", "творческий", "креатив"}
        },
        "social": {
            "patterns": [
                r"привет\s*!?",
                r"как\s+(дела|ты)",
                r"давай\s+поговорим",
                r"поболтаем\s*",
                r"расскажи\s+о\s+себе",
                r"ты\s+(кто|как)"
            ],
            "keywords": {"привет", "поговорим", "поболтаем", "общение", "разговор"}
        },
        "emotional": {
            "patterns": [
                r"мне\s+(грустно|плохо|тяжело)",
                r"поддержи\s+",
                r"помоги\s+справиться",
                r"я\s+(расстроен|устал|переживаю)",
                r"нужна\s+поддержка",
                r"совет\s+"
            ],
            "keywords": {"грустно", "плохо", "поддержи", "помощь", "совет", "тяжело"}
        },
        "decision": {
            "patterns": [
                r"что\s+выбрать",
                r"какой\s+лучше",
                r"стоит\s+ли",
                r"помоги\s+выбрать",
                r"твое\s+мнение",
                r"как\s+поступить"
            ],
            "keywords": {"выбрать", "лучше", "стоит", "мнение", "решение", "поступить"}
        }
    }
    
    # Urgency indicators
    URGENCY_INDICATORS = {
        "high": {
            "words": ["срочно", "быстро", "немедленно", "сейчас", "urgent", "asap"],
            "patterns": [r"!\s*!+", r"[A-Z]{3,}"]
        },
        "medium": {
            "words": ["важно", "нужно", "требуется", "желательно"],
            "patterns": []
        },
        "low": {
            "words": ["когда-нибудь", "потом", "не спеша", "при возможности"],
            "patterns": []
        }
    }
    
    # Priority indicators
    PRIORITY_INDICATORS = {
        "high": ["очень", "крайне", "чрезвычайно", "супер", "мега"],
        "medium": ["довольно", "весьма", "достаточно"],
        "low": ["немного", "чуть-чуть", "слегка"]
    }
    
    def extract(self, text: str, intent: str = None, emotion: dict = None) -> GoalResult:
        """
        Extract goal from text.
        
        Args:
            text: Input text
            intent: Pre-detected intent (optional)
            emotion: Pre-detected emotion (optional)
            
        Returns:
            GoalResult with extracted goal
        """
        text_lower = text.lower().strip()
        words = set(re.findall(r'\w+', text_lower))
        
        # Detect goal type
        goal_type, type_confidence = self._detect_goal_type(text_lower, words)
        
        # Extract goal statement
        goal = self._extract_goal_statement(text, goal_type)
        
        # Extract subgoals
        subgoals = self._extract_subgoals(text, goal_type)
        
        # Determine required actions
        required_actions = self._determine_actions(text, goal_type)
        
        # Calculate priority
        priority = self._calculate_priority(words, emotion)
        
        # Calculate urgency
        urgency = self._calculate_urgency(text_lower, words, emotion)
        
        # Adjust based on intent
        if intent:
            goal_type, goal = self._adjust_for_intent(goal_type, goal, intent, text)
        
        return GoalResult(
            goal=goal,
            goal_type=goal_type,
            confidence=type_confidence,
            subgoals=subgoals,
            required_actions=required_actions,
            priority=priority,
            urgency=urgency
        )
    
    def _detect_goal_type(self, text: str, words: set) -> tuple:
        """Detect goal type from text."""
        best_type = "unknown"
        best_score = 0.0
        
        for goal_type, data in self.GOAL_PATTERNS.items():
            patterns = data["patterns"]
            keywords = data["keywords"]
            
            # Pattern matching
            pattern_score = 0
            for pattern in patterns:
                if re.search(pattern, text):
                    pattern_score = 1.0
                    break
            
            # Keyword matching
            keyword_matches = len(words & keywords)
            keyword_score = min(1.0, keyword_matches / 2)
            
            # Combined score
            combined = pattern_score * 0.7 + keyword_score * 0.3
            
            if combined > best_score:
                best_score = combined
                best_type = goal_type
        
        return best_type, max(0.3, best_score)
    
    def _extract_goal_statement(self, text: str, goal_type: str) -> str:
        """Extract the main goal statement from text."""
        # Remove common filler words
        fillers = [
            "привет", "здравствуй", "пожалуйста", "спасибо",
            "ммм", "эээ", "ну", "как бы", "типа"
        ]
        
        cleaned = text
        for filler in fillers:
            cleaned = re.sub(r'\b' + filler + r'\b', '', cleaned, flags=re.IGNORECASE)
        
        cleaned = ' '.join(cleaned.split()).strip()
        
        # If we have a clear verb-object structure, extract it
        verb_patterns = [
            (r"(сделай|выполни|помоги)\s+(.+?)(?:\s*$|[,.!?])", "action"),
            (r"(расскажи|объясни|опиши)\s+(.+?)(?:\s*$|[,.!?])", "info"),
            (r"(придумай|создай|сгенерируй)\s+(.+?)(?:\s*$|[,.!?])", "creative"),
            (r"хочу\s+(.+?)(?:\s*$|[,.!?])", "desire"),
            (r"нужно\s+(.+?)(?:\s*$|[,.!?])", "need")
        ]
        
        for pattern, ptype in verb_patterns:
            match = re.search(pattern, cleaned, flags=re.IGNORECASE)
            if match:
                return match.group(2).strip()
        
        # Fallback: return cleaned text
        return cleaned[:200] if cleaned else "general interaction"
    
    def _extract_subgoals(self, text: str, goal_type: str) -> List[str]:
        """Extract subgoals from text."""
        subgoals = []
        
        # Look for conjunctions that indicate multiple goals
        conjunctions = ["и", "также", "еще", "а также", "плюс"]
        
        parts = re.split(r'\s*[,.!?;]\s*', text)
        
        for part in parts[1:]:  # Skip first part (main goal)
            part = part.strip()
            if len(part) > 5:  # Meaningful length
                # Check if it contains a goal-like structure
                for conj in conjunctions:
                    if part.lower().startswith(conj):
                        part = part[len(conj):].strip()
                        break
                
                if len(part) > 3:
                    subgoals.append(part[:100])
        
        return subgoals[:3]  # Max 3 subgoals
    
    def _determine_actions(self, text: str, goal_type: str) -> List[str]:
        """Determine required actions to fulfill goal."""
        actions = []
        
        action_map = {
            "informational": ["search_knowledge", "explain", "provide_context"],
            "task": ["analyze_request", "execute_action", "verify_result"],
            "creative": ["brainstorm", "generate_options", "refine_output"],
            "social": ["greet", "engage_conversation", "build_rapport"],
            "emotional": ["listen", "empathize", "support", "advise"],
            "decision": ["analyze_options", "compare", "recommend"]
        }
        
        actions = action_map.get(goal_type, ["process_input"])
        
        # Add specific actions based on text
        text_lower = text.lower()
        if "пример" in text_lower:
            actions.append("provide_examples")
        if "сравн" in text_lower:
            actions.append("compare")
        if "список" in text_lower or "перечисл" in text_lower:
            actions.append("list_items")
        
        return actions
    
    def _calculate_priority(self, words: set, emotion: dict = None) -> float:
        """Calculate goal priority."""
        priority = 0.5  # baseline
        
        # Check priority indicators
        for level, indicators in self.PRIORITY_INDICATORS.items():
            matches = words & set(indicators)
            if matches:
                if level == "high":
                    priority += 0.3
                elif level == "medium":
                    priority += 0.1
                elif level == "low":
                    priority -= 0.2
        
        # Emotion influence
        if emotion:
            anger = emotion.get("anger", 0)
            sadness = emotion.get("sadness", 0)
            if anger > 0.5 or sadness > 0.5:
                priority += 0.2
        
        return max(0.0, min(1.0, priority))
    
    def _calculate_urgency(self, text: str, words: set, emotion: dict = None) -> float:
        """Calculate goal urgency."""
        urgency = 0.5  # baseline
        
        # Check urgency indicators
        for level, data in self.URGENCY_INDICATORS.items():
            word_matches = words & set(data["words"])
            pattern_matches = any(re.search(p, text) for p in data["patterns"])
            
            if word_matches or pattern_matches:
                if level == "high":
                    urgency += 0.4
                elif level == "medium":
                    urgency += 0.15
                elif level == "low":
                    urgency -= 0.3
        
        # Emotion influence
        if emotion:
            anger = emotion.get("anger", 0)
            fear = emotion.get("fear", 0)
            if anger > 0.6 or fear > 0.6:
                urgency += 0.2
        
        return max(0.0, min(1.0, urgency))
    
    def _adjust_for_intent(
        self,
        goal_type: str,
        goal: str,
        intent: str,
        text: str
    ) -> tuple:
        """Adjust goal based on detected intent."""
        # Intent-Goal mapping
        intent_to_goal_type = {
            "query": "informational",
            "request": "task",
            "creative": "creative",
            "chat": "social",
            "opinion": "decision",
            "problem": "task"
        }
        
        if intent in intent_to_goal_type:
            mapped_type = intent_to_goal_type[intent]
            # Only adjust if confidence is low
            if goal_type == "unknown":
                goal_type = mapped_type
        
        return goal_type, goal

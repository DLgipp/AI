"""
Topic Detection Module - Extracts and embeds topics from input.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
import re


@dataclass
class TopicResult:
    """Detected topic with embedding and metadata."""
    primary_topic: str
    confidence: float = 1.0
    topic_vector: List[float] = field(default_factory=list)
    related_topics: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    category: str = "general"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "primary_topic": self.primary_topic,
            "confidence": self.confidence,
            "topic_vector": self.topic_vector,
            "related_topics": self.related_topics,
            "keywords": self.keywords,
            "category": self.category
        }


class TopicDetector:
    """
    Topic detection using keyword matching and simple embeddings.
    Can be extended with ML models (BERT, etc.) for better embeddings.
    """
    
    # Topic categories with keywords
    TOPIC_CATEGORIES = {
        "technology": {
            "keywords": [
                "компьютер", "программа", "код", "разработка", "софт", "приложение",
                "интернет", "сайт", "сервер", "база", "данные", "алгоритм", "ai",
                "нейросеть", "машинное", "обучение", "технология", "гаджет", "смартфон",
                "python", "javascript", "linux", "windows", "api", "docker"
            ],
            "topics": ["programming", "software", "hardware", "ai_ml", "web", "mobile"]
        },
        "science": {
            "keywords": [
                "наука", "исследование", "эксперимент", "теория", "гипотеза",
                "физика", "химия", "биология", "математика", "космос", "вселенная",
                "атом", "молекула", "энергия", "формула", "уравнение"
            ],
            "topics": ["physics", "chemistry", "biology", "math", "astronomy", "research"]
        },
        "entertainment": {
            "keywords": [
                "фильм", "кино", "музыка", "песня", "игра", "сериал", "актер",
                "режиссер", "альбом", "концерт", "шоу", "юмор", "комедия", "драма",
                "книга", "роман", "писатель", "литература"
            ],
            "topics": ["movies", "music", "games", "tv", "books", "humor"]
        },
        "lifestyle": {
            "keywords": [
                "здоровье", "спорт", "фитнес", "еда", "диета", "сон", "отдых",
                "путешествие", "отпуск", "хобби", "стиль", "мода", "красота",
                "дом", "семья", "отношения", "дружба", "любовь"
            ],
            "topics": ["health", "fitness", "food", "travel", "relationships", "home"]
        },
        "work": {
            "keywords": [
                "работа", "бизнес", "проект", "задача", "дедлайн", "встреча",
                "коллега", "менеджер", "клиент", "зарплата", "карьера", "офис",
                "предприниматель", "стартап", "компания", "организация"
            ],
            "topics": ["career", "business", "projects", "management", "finance"]
        },
        "education": {
            "keywords": [
                "учеба", "школа", "университет", "курс", "лекция", "экзамен",
                "знания", "навыки", "обучение", "тренинг", "сертификат", "диплом",
                "студент", "преподаватель", "учитель"
            ],
            "topics": ["school", "university", "courses", "skills", "certification"]
        },
        "news": {
            "keywords": [
                "новости", "событие", "происшествие", "политика", "экономика",
                "общество", "мир", "страна", "правительство", "выборы", "кризис"
            ],
            "topics": ["politics", "economy", "society", "world", "local"]
        },
        "philosophy": {
            "keywords": [
                "смысл", "жизнь", "смерть", "бог", "религия", "вера", "душа",
                "сознание", "мышление", "этика", "мораль", "ценности", "истина",
                "существование", "реальность", "природа"
            ],
            "topics": ["existence", "ethics", "religion", "consciousness", "values"]
        },
        "emotions": {
            "keywords": [
                "чувство", "эмоция", "настроение", "переживание", "стресс",
                "тревога", "радость", "грусть", "гнев", "страх", "любовь",
                "счастье", "депрессия", "мотивация", "вдохновение"
            ],
            "topics": ["feelings", "mental_health", "mood", "motivation"]
        }
    }
    
    # Simple topic vectors (placeholder for real embeddings)
    # In production, use BERT/SentenceTransformers for real embeddings
    TOPIC_VECTORS = {
        "programming": [0.8, 0.1, 0.2, 0.6, 0.3],
        "software": [0.7, 0.2, 0.1, 0.5, 0.2],
        "hardware": [0.6, 0.3, 0.4, 0.2, 0.1],
        "ai_ml": [0.9, 0.2, 0.3, 0.7, 0.4],
        "web": [0.5, 0.4, 0.2, 0.6, 0.3],
        "mobile": [0.5, 0.3, 0.3, 0.5, 0.2],
        "physics": [0.3, 0.8, 0.2, 0.4, 0.3],
        "chemistry": [0.2, 0.7, 0.3, 0.3, 0.2],
        "biology": [0.2, 0.7, 0.4, 0.2, 0.3],
        "math": [0.4, 0.6, 0.1, 0.5, 0.2],
        "astronomy": [0.3, 0.8, 0.5, 0.3, 0.4],
        "research": [0.5, 0.7, 0.3, 0.4, 0.3],
        "movies": [0.2, 0.3, 0.8, 0.2, 0.1],
        "music": [0.1, 0.2, 0.9, 0.1, 0.2],
        "games": [0.3, 0.4, 0.7, 0.3, 0.2],
        "tv": [0.2, 0.3, 0.8, 0.2, 0.1],
        "books": [0.2, 0.4, 0.7, 0.3, 0.2],
        "humor": [0.1, 0.2, 0.6, 0.4, 0.1],
        "health": [0.3, 0.4, 0.2, 0.3, 0.8],
        "fitness": [0.4, 0.3, 0.3, 0.2, 0.7],
        "food": [0.2, 0.2, 0.3, 0.1, 0.6],
        "travel": [0.3, 0.3, 0.4, 0.5, 0.5],
        "relationships": [0.2, 0.3, 0.3, 0.6, 0.7],
        "home": [0.3, 0.2, 0.2, 0.4, 0.5],
        "career": [0.5, 0.4, 0.3, 0.4, 0.4],
        "business": [0.6, 0.3, 0.4, 0.5, 0.3],
        "projects": [0.5, 0.4, 0.3, 0.5, 0.2],
        "management": [0.5, 0.3, 0.4, 0.6, 0.3],
        "finance": [0.4, 0.3, 0.3, 0.5, 0.4],
        "school": [0.3, 0.5, 0.3, 0.4, 0.3],
        "university": [0.4, 0.6, 0.3, 0.4, 0.3],
        "courses": [0.4, 0.5, 0.3, 0.4, 0.3],
        "skills": [0.4, 0.4, 0.3, 0.5, 0.4],
        "certification": [0.4, 0.4, 0.2, 0.4, 0.3],
        "politics": [0.3, 0.4, 0.3, 0.7, 0.5],
        "economy": [0.4, 0.4, 0.3, 0.6, 0.4],
        "society": [0.3, 0.4, 0.4, 0.7, 0.5],
        "world": [0.3, 0.4, 0.4, 0.8, 0.4],
        "local": [0.2, 0.3, 0.3, 0.6, 0.3],
        "existence": [0.3, 0.5, 0.4, 0.5, 0.6],
        "ethics": [0.3, 0.4, 0.4, 0.6, 0.7],
        "religion": [0.2, 0.4, 0.3, 0.5, 0.8],
        "consciousness": [0.4, 0.6, 0.4, 0.5, 0.6],
        "values": [0.3, 0.4, 0.4, 0.6, 0.7],
        "feelings": [0.2, 0.3, 0.5, 0.4, 0.6],
        "mental_health": [0.3, 0.4, 0.4, 0.4, 0.8],
        "mood": [0.2, 0.3, 0.5, 0.3, 0.5],
        "motivation": [0.4, 0.4, 0.5, 0.4, 0.6]
    }
    
    def detect(self, text: str) -> TopicResult:
        """
        Detect topic from text.
        
        Args:
            text: Input text
            
        Returns:
            TopicResult with detected topic and metadata
        """
        text_lower = text.lower()
        words = set(re.findall(r'\w{3,}', text_lower))  # words with 3+ chars
        
        best_category = "general"
        best_topic = "general"
        best_score = 0.0
        matched_keywords = []
        related_topics = []
        
        # Find best matching category and topic
        for category, data in self.TOPIC_CATEGORIES.items():
            keywords = set(data["keywords"])
            topics = data["topics"]
            
            # Count keyword matches
            matches = words & keywords
            score = len(matches) / len(keywords) if keywords else 0
            
            if score > best_score or (score == best_score and len(matches) > len(matched_keywords)):
                best_score = score
                best_category = category
                matched_keywords = list(matches)
                
                # Select best topic within category
                if topics:
                    # Simple heuristic: use first topic or based on specific keywords
                    best_topic = self._select_best_topic(topics, matches)
                    related_topics = [t for t in topics if t != best_topic]
        
        # Get topic vector
        topic_vector = self.TOPIC_VECTORS.get(best_topic, [0.5] * 5)
        
        # Normalize confidence
        confidence = min(1.0, best_score * 5) if best_score > 0 else 0.3
        
        # If no good match, default to general
        if best_score < 0.1:
            best_topic = "general"
            best_category = "general"
            topic_vector = [0.5] * 5
            confidence = 0.3
        
        return TopicResult(
            primary_topic=best_topic,
            confidence=confidence,
            topic_vector=topic_vector,
            related_topics=related_topics[:3],  # top 3 related
            keywords=matched_keywords[:5],  # top 5 keywords
            category=best_category
        )
    
    def _select_best_topic(self, topics: List[str], matched_keywords: set) -> str:
        """Select best topic from category based on matched keywords."""
        # Simplified: just return first topic
        # In production, use more sophisticated matching
        return topics[0] if topics else "general"
    
    def get_embedding(self, text: str) -> List[float]:
        """
        Get topic embedding for text.
        
        Args:
            text: Input text
            
        Returns:
            Topic vector (embedding)
        """
        result = self.detect(text)
        return result.topic_vector

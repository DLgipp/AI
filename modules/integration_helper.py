"""
Integration Helper - Вспомогательные функции для интеграции когнитивного пайплайна.

Этот модуль предоставляет упрощённый интерфейс для использования
когнитивного пайплайна в существующем коде.
"""

from typing import Optional, Dict, Any, List
import asyncio


class CognitiveAssistant:
    """
    Упрощённый интерфейс для работы с когнитивным пайплайном.
    
    Пример использования:
        assistant = CognitiveAssistant()
        response = await assistant.chat("Привет! Как дела?")
        print(response.text)
    """
    
    def __init__(
        self,
        session_id: str = "default",
        user_id: str = "user",
        assistant_name: str = "Акари"
    ):
        from modules.cognitive_pipeline import CognitivePipeline
        
        self.pipeline = CognitivePipeline(
            session_id=session_id,
            user_id=user_id,
            assistant_name=assistant_name
        )
        self._last_result: Optional[Dict[str, Any]] = None
    
    async def chat(
        self,
        text: str,
        voice_features: Optional[Dict[str, float]] = None,
        silence_duration: float = 0.0
    ) -> "ChatResponse":
        """
        Отправить сообщение и получить ответ.
        
        Args:
            text: Текст сообщения
            voice_features: Характеристики голоса (опционально)
            silence_duration: Длительность тишины до сообщения
            
        Returns:
            ChatResponse с ответом и метаданными
        """
        # Обработка через пайплайн
        result = await self.pipeline.process(
            text=text,
            voice_features=voice_features,
            silence_duration=silence_duration
        )
        
        self._last_result = result
        
        # Если есть ошибка
        if result.get("error"):
            return ChatResponse(
                text=f"[Ошибка: {result.get('error')}]",
                metadata=result
            )
        
        # Генерация ответа через LLM (внешний вызов)
        llm_response = await self._generate_llm_response(
            system_prompt=result.get("system_prompt", ""),
            user_prompt=text,
            history=result.get("history", [])
        )
        
        # Пост-обработка
        output = self.pipeline.process_llm_response(
            llm_response=llm_response,
            pipeline_result=result
        )
        
        return ChatResponse(
            text=output["text"],
            adjustments=output.get("style_adjustments", {}),
            metadata=result
        )
    
    async def _generate_llm_response(
        self,
        system_prompt: str,
        user_prompt: str,
        history: List[Dict[str, str]]
    ) -> str:
        """Генерация ответа через LLM."""
        from modules.llm.ollama_client import chat
        from config import MODEL_NAME, MAX_TOKENS
        
        messages = [
            {"role": "system", "content": system_prompt},
            *history[-10:],
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            response = chat(
                model=MODEL_NAME,
                messages=messages,
                options={
                    "temperature": 0.7,
                    "num_predict": MAX_TOKENS,
                }
            )
            return response["message"]["content"]
        except Exception as e:
            return f"[Ошибка LLM: {e}]"
    
    def process_feedback(self, feedback: str) -> Dict[str, Any]:
        """
        Обработать обратную связь от пользователя.
        
        Args:
            feedback: Текст обратной связи
            
        Returns:
            Результат обработки
        """
        if not self._last_result:
            return {"error": "No previous conversation"}
        
        return self.pipeline.process_user_feedback(
            feedback=feedback,
            pipeline_result=self._last_result
        )
    
    def get_personality_state(self) -> Dict[str, Any]:
        """Получить текущее состояние личности."""
        state = self.pipeline.personality.get_state()
        return {
            "traits": {
                "openness": state.openness,
                "conscientiousness": state.conscientiousness,
                "extraversion": state.extraversion,
                "agreeableness": state.agreeableness,
                "neuroticism": state.neuroticism,
                "curiosity": state.curiosity,
                "creativity": state.creativity,
                "empathy": state.empathy,
                "humor": state.humor,
                "assertiveness": state.assertiveness
            },
            "values": state.values,
            "mood": {
                "valence": state.mood_valence,
                "arousal": state.mood_arousal
            },
            "dominant_trait": state.get_dominant_trait()
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получить статистику сессии."""
        return self.pipeline.get_statistics()


class ChatResponse:
    """Ответ ассистента."""
    
    def __init__(
        self,
        text: str,
        adjustments: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.text = text
        self.adjustments = adjustments or {}
        self.metadata = metadata or {}
    
    @property
    def emotion(self) -> Optional[Dict[str, float]]:
        """Распознанная эмоция пользователя."""
        return self.metadata.get("interpretation", {}).get("emotion_full")
    
    @property
    def intent(self) -> Optional[str]:
        """Распознанное намерение пользователя."""
        return self.metadata.get("interpretation", {}).get("intent")
    
    @property
    def topic(self) -> Optional[str]:
        """Распознанная тема."""
        return self.metadata.get("interpretation", {}).get("topic", {}).get("primary_topic")
    
    @property
    def strategy(self) -> Optional[str]:
        """Использованная стратегия ответа."""
        return self.metadata.get("decision", {}).get("strategy")
    
    @property
    def stance(self) -> Optional[Dict[str, Any]]:
        """Позиция личности при ответе."""
        return self.metadata.get("stance")
    
    def __str__(self) -> str:
        return self.text
    
    def __repr__(self) -> str:
        return f"ChatResponse(text='{self.text[:50]}...', strategy={self.strategy})"


# =========================
# БЫСТРЫЙ СТАРТ
# =========================

async def quick_chat(text: str) -> str:
    """
    Быстрый чат с ассистентом (одна строка).
    
    Пример:
        response = await quick_chat("Привет!")
        print(response)
    """
    assistant = CognitiveAssistant()
    response = await assistant.chat(text)
    return response.text


def create_assistant(
    session_id: str = "default",
    user_id: str = "user",
    assistant_name: str = "Акари"
) -> CognitiveAssistant:
    """
    Создать нового ассистента.
    
    Пример:
        assistant = create_assistant(session_id="my_session")
    """
    return CognitiveAssistant(
        session_id=session_id,
        user_id=user_id,
        assistant_name=assistant_name
    )


# =========================
# ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ
# =========================

async def example_basic():
    """Базовый пример использования."""
    assistant = CognitiveAssistant()
    
    response = await assistant.chat("Привет! Расскажи что-нибудь интересное.")
    print(f"Ассистент: {response.text}")
    print(f"Стратегия: {response.strategy}")
    print(f"Тема: {response.topic}")


async def example_with_feedback():
    """Пример с обратной связью."""
    assistant = CognitiveAssistant()
    
    # Первое сообщение
    response1 = await assistant.chat("Помоги решить задачу по математике")
    print(f"Ассистент: {response1.text}")
    
    # Обратная связь
    feedback_result = assistant.process_feedback("Спасибо, очень помогло!")
    print(f"Вознаграждение: {feedback_result['reward']['value']}")


async def example_personality():
    """Пример проверки личности."""
    assistant = CognitiveAssistant()
    
    # Проверка начального состояния
    state = assistant.get_personality_state()
    print(f"Доминирующая черта: {state['dominant_trait']}")
    print(f"Настроение: {state['mood']['valence']:+.2f}")
    
    # Диалог
    await assistant.chat("Мне сегодня грустно...")
    
    # Проверка после диалога
    state = assistant.get_personality_state()
    print(f"Настроение после: {state['mood']['valence']:+.2f}")


if __name__ == "__main__":
    # Запуск примера
    asyncio.run(example_basic())

"""
LLM Service Module - Сервис для работы с языковой моделью.

Инкапсулирует всю логику работы с LLM (Ollama).
"""

import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class LLMRequest:
    """Запрос к LLM."""
    system_prompt: str
    user_prompt: str
    history: List[Dict[str, str]]
    temperature: float = 0.7
    max_tokens: int = 150
    
    def to_messages(self) -> List[Dict[str, str]]:
        """Преобразовать в формат messages для Ollama."""
        return [
            {"role": "system", "content": self.system_prompt},
            *self.history[-10:],  # Последние 10 сообщений
            {"role": "user", "content": self.user_prompt}
        ]


@dataclass
class LLMResponse:
    """Ответ от LLM."""
    content: str
    latency_ms: float
    tokens: int = 0
    model: str = ""
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def success(self) -> bool:
        """Успешен ли запрос."""
        return self.error is None and len(self.content) > 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "latency_ms": self.latency_ms,
            "tokens": self.tokens,
            "model": self.model,
            "error": self.error,
            "success": self.success,
            "metadata": self.metadata
        }


class LLMService:
    """
    Сервис для работы с LLM.
    
    Инкапсулирует:
    - Подключение к Ollama
    - Формирование запросов
    - Обработку ответов
    - Логирование
    - Обработку ошибок
    """
    
    def __init__(
        self,
        model_name: str = "gpt-oss:120b-cloud",
        default_temperature: float = 0.7,
        default_max_tokens: int = 150
    ):
        self.model_name = model_name
        self.default_temperature = default_temperature
        self.default_max_tokens = default_max_tokens
        
        # Импорты (ленивая загрузка)
        self._chat = None
        self._log = None
    
    def _get_chat(self):
        """Ленивая загрузка chat функции."""
        if self._chat is None:
            try:
                from ollama import chat
                self._chat = chat
            except ImportError:
                raise ImportError("Ollama not installed. Run: pip install ollama")
        return self._chat
    
    def _get_log(self):
        """Ленивая загрузка логгера."""
        if self._log is None:
            try:
                from modules.stt.logger import log
                self._log = log
            except ImportError:
                # Заглушка если логгер недоступен
                self._log = lambda msg, **kwargs: print(msg)
        return self._log
    
    def generate(
        self,
        request: LLMRequest
    ) -> LLMResponse:
        """
        Синхронная генерация ответа.
        
        Args:
            request: Запрос к LLM
            
        Returns:
            LLMResponse с ответом
        """
        log = self._get_log()
        chat = self._get_chat()
        
        start_time = time.time()
        
        try:
            # Формирование messages
            messages = request.to_messages()

            # Логирование (основное в main.py, здесь только если нужно)
            # log(f"LLM: {len(messages)} messages, system={len(request.system_prompt)} chars",
            #     role="DEBUG", stage="LLM")

            if len(request.system_prompt) > 100:
                log(f"System prompt preview: {request.system_prompt[:200]}...",
                    role="DEBUG", stage="LLM")
            
            # Вызов LLM
            response = chat(
                model=self.model_name,
                messages=messages,
                options={
                    "temperature": request.temperature,
                    "num_predict": request.max_tokens,
                }
            )

            # Обработка ответа
            latency_ms = (time.time() - start_time) * 1000

            # Ollama ChatResponse - извлекаем content
            # Структура: response.message.content (Message object)
            content = ""
            
            # Проверяем что response имеет message атрибут
            if hasattr(response, 'message'):
                msg = response.message
                log(f"DEBUG: msg={msg}, type={type(msg)}", role="DEBUG", stage="LLM")
                
                # Message object имеет content атрибут
                if hasattr(msg, 'content'):
                    content = msg.content
                    log(f"DEBUG: content found, len={len(content)}", role="DEBUG", stage="LLM")
                elif hasattr(msg, '__getitem__') and 'content' in msg:
                    content = msg['content']
                    log(f"DEBUG: content from dict, len={len(content)}", role="DEBUG", stage="LLM")
            
            # Если не нашли, пробуем как dict
            if not content and isinstance(response, dict):
                try:
                    content = response["message"]["content"]
                    log(f"DEBUG: content from response dict, len={len(content)}", role="DEBUG", stage="LLM")
                except (KeyError, TypeError):
                    pass
            
            # Извлечение метаданных
            tokens = 0
            if hasattr(response, 'prompt_eval_count'):
                tokens = getattr(response, 'prompt_eval_count', 0)
            elif isinstance(response, dict):
                tokens = response.get("eval_count", 0)

            log(f"LLM response: {latency_ms:.1f} ms, {len(content)} chars, {tokens} tokens",
                role="PIPELINE", stage="LLM")
            
            if not content:
                log("WARNING: Empty content from LLM!", role="WARN", stage="LLM")
                # Дополнительная отладка
                if hasattr(response, 'message'):
                    log(f"DEBUG: message type={type(response.message)}, dir={dir(response.message)[:5]}",
                        role="DEBUG", stage="LLM")
            
            return LLMResponse(
                content=content,
                latency_ms=latency_ms,
                tokens=tokens,
                model=self.model_name,
                metadata={
                    "messages_count": len(messages),
                    "system_prompt_length": len(request.system_prompt),
                    "user_prompt_length": len(request.user_prompt)
                }
            )
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            log(f"LLM error: {e}", role="ERROR", stage="LLM")
            
            return LLMResponse(
                content="",
                latency_ms=latency_ms,
                error=str(e),
                model=self.model_name
            )
    
    async def generate_async(
        self,
        request: LLMRequest
    ) -> LLMResponse:
        """
        Асинхронная генерация ответа.
        
        Args:
            request: Запрос к LLM
            
        Returns:
            LLMResponse с ответом
        """
        import asyncio
        
        loop = asyncio.get_event_loop()
        
        # Запуск в executor
        return await loop.run_in_executor(
            None,
            lambda: self.generate(request)
        )
    
    def generate_simple(
        self,
        system_prompt: str,
        user_prompt: str,
        history: Optional[List[Dict[str, str]]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Упрощённый интерфейс для быстрой генерации.
        
        Args:
            system_prompt: Системный промпт
            user_prompt: Пользовательский ввод
            history: Опциональная история диалога
            temperature: Температура (по умолчанию default)
            max_tokens: Максимум токенов (по умолчанию default)
            
        Returns:
            Текст ответа или пустая строка при ошибке
        """
        request = LLMRequest(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            history=history or [],
            temperature=temperature or self.default_temperature,
            max_tokens=max_tokens or self.default_max_tokens
        )
        
        response = self.generate(request)
        
        if response.success:
            return response.content
        else:
            return f"[LLM Error: {response.error}]"


# Глобальный сервис (singleton)
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Получить глобальный LLM сервис."""
    global _llm_service
    if _llm_service is None:
        from config import MODEL_NAME, MAX_TOKENS
        _llm_service = LLMService(
            model_name=MODEL_NAME,
            default_max_tokens=MAX_TOKENS
        )
    return _llm_service


def generate_llm_response(
    system_prompt: str,
    user_prompt: str,
    history: Optional[List[Dict[str, str]]] = None
) -> str:
    """
    Быстрая функция для генерации ответа.
    
    Args:
        system_prompt: Системный промпт
        user_prompt: Пользовательский ввод
        history: Опциональная история диалога
        
    Returns:
        Текст ответа
    """
    service = get_llm_service()
    return service.generate_simple(system_prompt, user_prompt, history)


async def generate_llm_response_async(
    system_prompt: str,
    user_prompt: str,
    history: Optional[List[Dict[str, str]]] = None
) -> str:
    """
    Асинхронная быстрая генерация.
    
    Args:
        system_prompt: Системный промпт
        user_prompt: Пользовательский ввод
        history: Опциональная история диалога
        
    Returns:
        Текст ответа
    """
    service = get_llm_service()
    request = LLMRequest(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        history=history or []
    )
    response = await service.generate_async(request)
    
    if response.success:
        return response.content
    else:
        return f"[LLM Error: {response.error}]"

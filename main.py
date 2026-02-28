"""
Main.py - Интегрированная версия с когнитивным пайплайном

Эта версия использует полную архитектуру эволюционирующего ИИ-ассистента:
- Perception Layer (восприятие)
- Interpretation Layer (понимание)
- Memory Layer (память)
- Personality Engine (личность)
- Decision Layer (решения)
- Prompt Builder (промпты)
- Behavior Layer (поведение)
- Evolution Layer (эволюция/RL)
"""

import asyncio
import time
from typing import Optional

# Оригинальные импорты
from modules.core.dialog_core import DialogueCore
from modules.tts.tts import speak_async
from modules.events.event_bus import EventBus
from modules.events.policy import ReactivePolicy
from modules.stt.controller import STTController
from modules.events.timers import SilenceTimer

# Импорты когнитивного пайплайна
from modules.cognitive_pipeline import CognitivePipeline
from modules.llm.llm_service import LLMService, LLMRequest, get_llm_service
from config import (
    SILENCE_TIMEOUT_SEC,
    MODEL_NAME,
    MAX_TOKENS,
    ASSISTANT_NAME,
    DEFAULT_SESSION_ID,
    DEFAULT_USER_ID
)

# Глобальные объекты
cognitive_pipeline: Optional[CognitivePipeline] = None
dialog: Optional[DialogueCore] = None
silence_timer: Optional[SilenceTimer] = None
llm_service: Optional[LLMService] = None


async def stt_loop(stt: STTController, loop):
    """Постоянный цикл STT."""
    while True:
        await loop.run_in_executor(None, stt.tick)
        await asyncio.sleep(0.02)


async def silence_loop(silence_timer: SilenceTimer):
    """Цикл таймера тишины."""
    while True:
        silence_timer.tick()
        await asyncio.sleep(0.1)


async def tts_loop(dialog: DialogueCore, silence_timer: SilenceTimer, loop=None):
    """Цикл произнесения ответов ассистента с выразительностью."""
    while True:
        assistant_msg = dialog.pop_next()
        if assistant_msg and assistant_msg["role"] == "assistant" and dialog.can_speak():
            dialog.set_speaking()
            
            # Получаем контекст выразительности из сообщения
            tts_context = assistant_msg.get("tts_context")
            
            if tts_context:
                from modules.tts.tts_expression import ExpressionContext
                context = ExpressionContext(**tts_context)
                await speak_async(assistant_msg["text"], silence_timer, context)
            else:
                await speak_async(assistant_msg["text"], silence_timer)
            
            dialog.set_listening()
        await asyncio.sleep(0.02)


async def generate_llm_response(
    system_prompt: str,
    user_prompt: str,
    history: list,
    silence_timer: SilenceTimer
) -> str:
    """
    Генерация ответа через LLM Service.

    Args:
        system_prompt: Системный промпт с личностью
        user_prompt: Пользовательский ввод
        history: История диалога
        silence_timer: Таймер активности

    Returns:
        Текст ответа
    """
    try:
        # Используем LLM Service
        global llm_service
        
        request = LLMRequest(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            history=history[-10:],  # Последние 10 сообщений
            temperature=0.7,
            max_tokens=500  # Увеличено с 150 для thinking моделей
        )
        
        # Логирование
        from modules.stt.logger import log
        log(f"LLM Service: {len(request.to_messages())} messages, "
            f"system={len(system_prompt)} chars",
            role="DEBUG", stage="LLM")
        
        if len(system_prompt) > 100:
            log(f"System prompt preview: {system_prompt[:200]}...",
                role="DEBUG", stage="LLM")
        
        # Генерация через сервис
        silence_timer.activity_start()
        response = llm_service.generate(request)
        silence_timer.activity_end()

        # Проверка ответа
        log(f"LLM response type: {type(response)}",
            role="DEBUG", stage="LLM")
        log(f"LLM content length: {len(response.content)}",
            role="DEBUG", stage="LLM")

        # Логирование thinking контента если есть
        if response.thinking:
            log(f"LLM thinking: {response.thinking}",
                role="DEBUG", stage="LLM")

        if response.error:
            log(f"LLM error from service: {response.error}",
                role="ERROR", stage="LLM")

        return response.content

    except Exception as e:
        from modules.stt.logger import log
        log(f"LLM error (cognitive): {e}", role="ERROR", stage="LLM")
        return "[Ошибка генерации ответа]"


async def llm_handler(event, dialog: DialogueCore, silence_timer: SilenceTimer):
    """
    Обработка пользовательского ввода через когнитивный пайплайн.
    
    Полный цикл:
    1. Perception → Interpretation → Memory → Personality → Decision → Prompt
    2. LLM Generation
    3. Behavior Processing
    4. Memory Storage
    """
    global cognitive_pipeline
    
    text = event.payload.get("text", "")
    silence_duration = time.time() - silence_timer._last_activity
    
    from modules.stt.logger import log
    log(f"Cognitive pipeline started for: {text[:50]}...", role="PIPELINE", stage="START")
    
    try:
        # ========== ШАГ 1: Обработка через когнитивный пайплайн ==========
        result = await cognitive_pipeline.process(
            text=text,
            voice_features=None,  # Можно добавить из STT
            silence_duration=silence_duration,
            interruption=False
        )
        
        # Проверка на ошибки
        if result.get("error"):
            log(f"Pipeline error: {result['error']}", role="ERROR", stage="PIPELINE")
            dialog.push_assistant_message("[Ошибка обработки]")
            return
        
        log(f"Pipeline stages: {result['stages']}", role="PIPELINE", stage="COMPLETE")
        
        # ========== ШАГ 2: Генерация ответа LLM ==========
        system_prompt = result.get("system_prompt", "")
        prompt = result.get("prompt", "")
        
        # Отладка: проверка промптов
        log(f"System prompt length: {len(system_prompt)}", role="DEBUG", stage="LLM")
        log(f"User prompt length: {len(prompt)}", role="DEBUG", stage="LLM")
        
        if not system_prompt:
            log("WARNING: Empty system prompt!", role="ERROR", stage="LLM")
        if not prompt:
            log("WARNING: Empty user prompt!", role="ERROR", stage="LLM")
        
        # Извлекаем историю из памяти
        history = cognitive_pipeline.memory.episodic.get_recent(
            session_id=cognitive_pipeline.session_id,
            limit=10
        )
        history_formatted = [
            {"role": "user" if m.event_type == "user_message" else "assistant", 
             "content": m.content}
            for m in history
        ]
        
        llm_response = await generate_llm_response(
            system_prompt=system_prompt,
            user_prompt=text,
            history=history_formatted,
            silence_timer=silence_timer
        )
        
        # ========== ШАГ 3: Пост-обработка через Behavior Layer ==========
        output = cognitive_pipeline.process_llm_response(
            llm_response=llm_response,
            pipeline_result=result
        )

        final_text = output["text"]
        adjustments = output.get("style_adjustments", {})
        tts_context = output.get("tts_context")

        log(f"Behavior adjustments: {adjustments}", role="PIPELINE", stage="BEHAVIOR")

        # ========== ШАГ 4: Сохранение в диалог и память ==========
        dialog.push_user_message(text)
        
        # Сохраняем сообщение с контекстом для TTS
        dialog.push_assistant_message(final_text, metadata={"tts_context": tts_context})
        
        log(f"Response pushed to dialog: {final_text}...", role="ASSISTANT", stage="COMPLETE")
        
        # ========== ШАГ 5: Логирование состояния личности ==========
        personality_stats = cognitive_pipeline.personality.memory.get_statistics()
        log(f"Personality: trait={personality_stats['dominant_trait']}, "
            f"mood={personality_stats['current_mood_valence']:+.2f}", 
            role="PIPELINE", stage="PERSONALITY")
        
    except Exception as e:
        log(f"Critical error in llm_handler: {e}", role="ERROR", stage="HANDLER")
        dialog.push_assistant_message("[Произошла ошибка при обработке запроса]")


async def process_user_feedback(text: str):
    """
    Обработка явной обратной связи от пользователя.
    
    Args:
        text: Текст обратной связи (например, "спасибо", "плохо")
    """
    global cognitive_pipeline
    
    # Определяем тип обратной связи
    feedback_keywords_positive = ["спасибо", "благодарю", "классно", "отлично", "хорошо", "помог"]
    feedback_keywords_negative = ["плохо", "ужасно", "бесполезно", "не помогло", "ошибка"]
    
    text_lower = text.lower()
    
    if any(kw in text_lower for kw in feedback_keywords_positive):
        reward_value = 0.8
        feedback_text = "positive"
    elif any(kw in text_lower for kw in feedback_keywords_negative):
        reward_value = -0.8
        feedback_text = "negative"
    else:
        return  # Не является явной обратной связью
    
    # Получаем последний результат пайплайна (из памяти)
    recent = cognitive_pipeline.memory.episodic.get_recent(
        session_id=cognitive_pipeline.session_id,
        limit=1
    )
    
    if recent:
        # Создаём псевдо-результат для обработки обратной связи
        pseudo_result = {
            "decision": {"strategy": "ANSWER_DIRECT"},
            "stance": cognitive_pipeline.personality.get_state().to_dict()
        }
        
        # Обрабатываем обратную связь
        feedback_result = cognitive_pipeline.process_user_feedback(
            feedback=feedback_text,
            pipeline_result=pseudo_result
        )
        
        from modules.stt.logger import log
        log(f"Feedback processed: reward={feedback_result['reward']['value']:.2f}, "
            f"evolution={feedback_result['evolution_event'] is not None}", 
            role="PIPELINE", stage="EVOLUTION")


async def main():
    """
    Основная функция запуска ассистента.
    """
    global cognitive_pipeline, dialog, silence_timer, llm_service

    # =========================
    # ИНФРАСТРУКТУРА
    # =========================
    loop = asyncio.get_running_loop()
    bus = EventBus(loop)
    silence_timer = SilenceTimer(bus, timeout_sec=SILENCE_TIMEOUT_SEC)
    dialog = DialogueCore(history_size=10)
    policy = ReactivePolicy(dialog, cooldown_sec=13.0)
    stt = STTController(bus, silence_timer)
    
    # =========================
    # LLM SERVICE
    # =========================
    llm_service = get_llm_service()
    from modules.stt.logger import log
    log(f"LLM Service initialized: {llm_service.model_name}", 
        role="SYSTEM", stage="INIT")

    # =========================
    # КОГНИТИВНЫЙ ПАЙПЛАЙН
    # =========================
    cognitive_pipeline = CognitivePipeline(
        session_id=DEFAULT_SESSION_ID,
        user_id=DEFAULT_USER_ID,
        assistant_name=ASSISTANT_NAME
    )
    
    # Инициализация личности из конфига
    from config import PERSONALITY_TRAITS, PERSONALITY_VALUES
    
    state = cognitive_pipeline.personality.get_state()
    
    # Применяем начальные черты из конфига
    for trait_name, value in PERSONALITY_TRAITS.items():
        cognitive_pipeline.personality.memory.update_trait(trait_name, value)
    
    # Применяем ценности из конфига
    for value_name, weight in PERSONALITY_VALUES.items():
        state.update_value(value_name, weight)
    cognitive_pipeline.personality.memory.save_state(state)
    
    from modules.stt.logger import log
    log(f"Cognitive pipeline initialized. Assistant: {ASSISTANT_NAME}", 
        role="SYSTEM", stage="INIT")
    log(f"Personality traits: {PERSONALITY_TRAITS}", role="SYSTEM", stage="INIT")
    
    # =========================
    # EVENT HANDLERS
    # =========================
    def user_text_handler(event):
        """Обработчик пользовательского текста."""
        result = llm_handler(event, dialog, silence_timer)
        if asyncio.iscoroutine(result):
            loop.call_soon_threadsafe(asyncio.create_task, result)
    
    def silence_handler(event):
        """Обработчик таймаута тишины."""
        # Можно добавить инициативные сообщения ассистента
        policy.handle_event(event)
    
    bus.subscribe("user_text", user_text_handler)
    bus.subscribe("silence_timeout", silence_handler)
    
    # =========================
    # СТАТИСТИКА ПРИ ЗАПУСКЕ
    # =========================
    stats = cognitive_pipeline.get_statistics()
    log(f"Session: {stats['session_id']}, User: {stats['user_id']}", 
        role="SYSTEM", stage="READY")
    
    # =========================
    # ЗАПУСК ПАРАЛЛЕЛЬНЫХ ЦИКЛОВ
    # =========================
    print("\n" + "="*60)
    print(f"🤖 {ASSISTANT_NAME} запущен с когнитивным пайплайном!")
    print("="*60)
    print(f"Личность: {list(PERSONALITY_TRAITS.keys())}")
    print(f"Сессия: {DEFAULT_SESSION_ID}")
    print("="*60 + "\n")
    
    await asyncio.gather(
        stt_loop(stt, loop),
        tts_loop(dialog, silence_timer, loop),
        silence_loop(silence_timer),
    )


if __name__ == "__main__":
    asyncio.run(main())

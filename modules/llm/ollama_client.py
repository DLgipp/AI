import asyncio
from ollama import chat
from config import SYSTEM_PROMPT, MAX_HISTORY, MODEL_NAME, MAX_TOKENS, MARIN_PERSONA
from modules.llm.logger import log_entry
from modules.stt.logger import log
from modules.memory.message_store import SQLiteMessageStore
from modules.memory.session_state import SQLiteSessionStateStore
import time

from modules.events.timers import SilenceTimer

message_store = SQLiteMessageStore()
session_state = SQLiteSessionStateStore()
SESSION_ID = "default"

def _generate_response_blocking(user_input, history: list, silence_timer: SilenceTimer):
    silence_timer.activity_start()
    """Оригинальная синхронная генерация ответа."""
    try:
        recent_history = message_store.load_recent(session_id=SESSION_ID, limit=MAX_HISTORY)
        session_data = session_state.get_all(SESSION_ID)

        system_prompt = f"""Ты — {MARIN_PERSONA['name']}, {MARIN_PERSONA['role']}. 
Стиль речи: {MARIN_PERSONA['style']}. 
Используй эмоциональные вставки: {', '.join(MARIN_PERSONA['speech_markers'])}. 
Текущее состояние диалога: {session_data}. 
{SYSTEM_PROMPT}"""

        prompt = [
            {"role": "system", "content": system_prompt},
            *recent_history,
            {"role": "user", "content": user_input},
        ]

        log(f"Sending prompt to LLM", role="PIPELINE", stage="LLM", payload=f"{len(user_input)} chars")
        start = time.time()

        response = chat(
            model=MODEL_NAME,
            messages=prompt,
            options={
                "temperature": 0.0,
                "num_predict": MAX_TOKENS,
            }
        )

        latency_ms = (time.time() - start) * 1000
        content = response["message"]["content"]

        message_store.save_message(SESSION_ID, "user", user_input)
        message_store.save_message(SESSION_ID, "assistant", content)
        session_state.set(SESSION_ID, "last_user_message", user_input)

        log(f"LLM response received", role="PIPELINE", stage="LLM", payload=f"{len(content)} chars, latency={latency_ms:.1f} ms")
        log(f"Response content: {content}", role="ASSISTANT", stage="LLM")
        log_entry({"prompt": user_input, "response": content, "latency_ms": latency_ms, "tokens": response.get("eval_count")})

        return content

    except Exception as e:
        log(f"LLM error: {e}", role="ERROR", stage="LLM")
        return "[LLM ERROR]"
    finally:
        silence_timer.activity_end()

async def generate_response_async(user_input, history: list, silence_timer):
    """Асинхронная обёртка для LLM."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _generate_response_blocking, user_input, history, silence_timer)

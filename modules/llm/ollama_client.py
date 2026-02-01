from ollama import chat
from config import SYSTEM_PROMPT, MAX_HISTORY, MODEL_NAME, MAX_TOKENS, MARIN_PERSONA
from modules.llm.history_manager import get_history, add_to_history
from modules.llm.logger import log_entry
from modules.stt.logger import log

from modules.llm.session_memory.memory_manager import SessionMemory

import time

session = SessionMemory(user_id="user_123")  # можно динамически подставлять user_id

def generate_response(user_input, history:list):
    try:
        # формируем системный промт с учетом личности
        last_topic = session.get("last_topic", "нет темы")
        user_name = session.get("user_name", "Пользователь")
        system_prompt = f"""Ты — {MARIN_PERSONA['name']}, {MARIN_PERSONA['role']}. Стиль речи: {MARIN_PERSONA['style']}. Используй эмоциональные вставки: {', '.join(MARIN_PERSONA['speech_markers'])}. {SYSTEM_PROMPT}  # общий системный контекст"""
        prompt = [
            {"role": "system", "content": system_prompt},
            *get_history(),
            {"role": "user", "content": user_input},
        ]

        log(f"Sending prompt to LLM", role="PIPELINE", stage="LLM", payload=f"{len(user_input)} chars")

        start = time.time()

        response = chat(
            model="llama3.1",
            messages=prompt,
            options={
                "temperature": 0.0,
                "num_predict": MAX_TOKENS,
            }
        )

        latency_ms = (time.time() - start) * 1000

        content = response["message"]["content"]
        add_to_history(user_input, content)

        session.set("last_topic", user_input)  # можно более умно определять тему
        session.set("last_response", content)

        log(f"LLM response received", role="PIPELINE", stage="LLM", payload=f"{len(content)} chars, latency={latency_ms:.1f} ms")
        log(f"Response content: {content}", role="ASSISTANT", stage="LLM")

        log_entry({
            "prompt": user_input,
            "response": content,
            "latency_ms": latency_ms,
            "tokens": response.get("eval_count"),
        })

        return content
    except Exception as e:
        log(f"LLM error: {e}", role="ERROR", stage="LLM")
        return "[LLM ERROR]"
from ollama import chat
from config import SYSTEM_PROMPT, MAX_HISTORY, MODEL_NAME, MAX_TOKENS
from modules.llm.history_manager import get_history, add_to_history
from modules.llm.logger import log_entry
from modules.stt.logger import log

import time

def generate_response(user_input, history:list):
    try:
        prompt = [
            {"role": "system", "content": SYSTEM_PROMPT},
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
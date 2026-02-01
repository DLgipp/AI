from ollama import chat
from config import SYSTEM_PROMPT, MAX_HISTORY, MODEL_NAME, MAX_TOKENS
from modules.llm.history_manager import get_history, add_to_history
from modules.llm.logger import log_entry

import time

def generate_response(user_input, history:list):
    prompt = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *get_history(),
        {"role": "user", "content": user_input},
    ]
    
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

    log_entry({
        "prompt": user_input,
        "response": content,
        "latency_ms": latency_ms,
        "tokens": response.get("eval_count"),
    })

    return content

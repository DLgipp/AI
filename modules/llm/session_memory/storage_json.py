import json, os

MEMORY_DIR = "memory"
os.makedirs(MEMORY_DIR, exist_ok=True)

def memory_path(user_id):
    return os.path.join(MEMORY_DIR, f"{user_id}.json")

def load_memory(user_id):
    path = memory_path(user_id)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_memory(user_id, memory):
    path = memory_path(user_id)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)

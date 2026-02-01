import json
from pathlib import Path

LOG_FILE = Path("data/log.json")
LOG_FILE.parent.mkdir(exist_ok=True)

def log_entry(entry):
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

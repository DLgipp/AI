from datetime import datetime
import sys

# ANSI цвета для консоли
COLORS = {
    "SYSTEM": "\033[90m",   # серый
    "USER": "\033[92m",     # зелёный
    "ASSISTANT": "\033[96m",# циан
    "PIPELINE": "\033[93m", # жёлтый
    "ERROR": "\033[91m",    # красный
    "ENDC": "\033[0m"
}

def log(message, role="SYSTEM", stage="", level="INFO", payload=None):
    timestamp = datetime.now().strftime("%H:%M:%S")
    color = COLORS.get(role, COLORS["SYSTEM"])
    payload_str = f" | payload: {payload}" if payload else ""
    output = f"{color}[{timestamp}] {level:5} {role:10} {stage:12} {message}{payload_str}{COLORS['ENDC']}"
    print(output, file=sys.stdout)

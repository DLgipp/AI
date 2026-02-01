# core/dialog_core.py

from collections import deque
from enum import Enum, auto
from typing import Optional, List, Dict


class AssistantState(Enum):
    LISTENING = auto()
    SPEAKING = auto()


class DialogueCore:
    def __init__(self, history_size: int = 10):
        # Очередь реплик (user / assistant)
        self._queue: deque[Dict[str, str]] = deque()

        # История последних N сообщений
        self._history: deque[Dict[str, str]] = deque(maxlen=history_size)

        # Состояние ассистента
        self._state: AssistantState = AssistantState.LISTENING

    # ---------- Очередь ----------

    def push_user_message(self, text: str) -> None:
        self._queue.append({"role": "user", "text": text})

    def push_assistant_message(self, text: str) -> None:
        self._queue.append({"role": "assistant", "text": text})

    def pop_next(self) -> Optional[Dict[str, str]]:
        if not self._queue:
            return None

        message = self._queue.popleft()
        self._history.append(message)
        return message

    # ---------- История ----------

    def get_history(self) -> List[Dict[str, str]]:
        return list(self._history)

    # ---------- Состояние ----------

    def can_speak(self) -> bool:
        return self._state == AssistantState.LISTENING

    def set_speaking(self) -> None:
        self._state = AssistantState.SPEAKING

    def set_listening(self) -> None:
        self._state = AssistantState.LISTENING

    def is_speaking(self) -> bool:
        return self._state == AssistantState.SPEAKING

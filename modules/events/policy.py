import time
from modules.core.dialog_core import DialogueCore
from modules.events.event import Event


class ReactivePolicy:
    def __init__(
        self,
        dialog: DialogueCore,
        cooldown_sec: float = 3.0
    ):
        self._dialog = dialog
        self._cooldown = cooldown_sec
        self._last_assistant_initiative = 0.0

    def handle_event(self, event: Event) -> None:
        if event.type == "silence_timeout":
            self._handle_silence(event)

    def _handle_silence(self, event: Event) -> None:
        now = time.time()

        # 1. Ассистент сейчас говорит — нельзя
        if self._dialog.is_speaking():
            return

        # 2. Кулдаун после инициативы
        if now - self._last_assistant_initiative < self._cooldown:
            return

        # 3. Нет истории — не лезем первыми
        if not self._dialog.get_history():
            return

        # === РЕШЕНИЕ: МОЖНО ГОВОРИТЬ ===
        self._last_assistant_initiative = now

        self._dialog.push_assistant_message(
            self._build_initiative_stub(event)
        )

    def _build_initiative_stub(self, event: Event) -> str:
        """
        Временная заглушка.
        На следующем шаге заменим на LLM.
        """
        duration = event.payload.get("duration", 0)
        return f"Ты давно молчишь ({duration} секунд). О чём продолжим?"

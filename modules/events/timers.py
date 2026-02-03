import time
from modules.events.event import Event
from modules.events.event_bus import EventBus


class SilenceTimer:
    def __init__(self, event_bus: EventBus, timeout_sec: float):
        self._bus = event_bus
        self._timeout = timeout_sec
        self._last_activity = time.time()
        self._triggered = False
        self._active_sources = 0  # ← ключевое

    def activity_start(self) -> None:
        """
        Вызывается при начале любой активности (LLM, TTS, STT).
        """
        self._active_sources += 1
        self._last_activity = time.time()
        self._triggered = False

    def activity_end(self) -> None:
        """
        Вызывается при завершении активности.
        """
        self._active_sources = max(0, self._active_sources - 1)
        self._last_activity = time.time()
        self._triggered = False

    def notify_activity(self) -> None:
        """
        Быстрое событие активности (например, звук, VAD).
        """
        self._last_activity = time.time()
        self._triggered = False

    def tick(self) -> None:
        if self._active_sources > 0:
            # Ассистент занят — тишины быть не может
            return

        elapsed = time.time() - self._last_activity
        if not self._triggered and elapsed >= self._timeout:
            self._triggered = True
            self._bus.emit(Event(
                type="silence_timeout",
                payload={"duration": int(elapsed)}
            ))


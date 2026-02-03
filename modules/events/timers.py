import time
from modules.events.event import Event
from modules.events.event_bus import EventBus


class SilenceTimer:
    def __init__(self, event_bus: EventBus, timeout_sec: float):
        self._bus = event_bus
        self._timeout = timeout_sec
        self._last_activity = time.time()
        self._triggered = False

    def notify_activity(self) -> None:
        """
        Вызывается при любой активности пользователя или ассистента.
        """
        self._last_activity = time.time()
        self._triggered = False

    def tick(self) -> None:
        """
        Должен вызываться регулярно (например, в main loop).
        """
        now = time.time()
        elapsed = now - self._last_activity

        if not self._triggered and elapsed >= self._timeout:
            self._triggered = True
            self._bus.emit(Event(
                type="silence_timeout",
                payload={"duration": int(elapsed)}
            ))

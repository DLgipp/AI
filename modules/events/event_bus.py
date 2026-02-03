from typing import Callable, Dict, List
from modules.events.event import Event
import asyncio

EventHandler = Callable[[Event], None]

class EventBus:
    def __init__(self, loop):
        self._subscribers: Dict[str, List[Callable]] = {}
        self.loop = loop  # главный loop

    def subscribe(self, event_type: str, handler: Callable):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def emit(self, event: Event):
        """Вызывает подписчиков события. Async handlers запускаются через create_task."""
        handlers = self._subscribers.get(event.type, [])
        #loop = asyncio.get_event_loop()  # главный loop
        print(f"[EventBus] emitting {event.type} to {len(handlers)} handlers")

        for handler in handlers:
            try:
                result = handler(event)
                if asyncio.iscoroutine(result):
                    # безопасный запуск из другого потока
                    self.loop.call_soon_threadsafe(asyncio.create_task, result)
            except Exception as e:
                print(f"[EventBus] handler error: {e}")

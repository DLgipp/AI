# core/events/event_bus.py

from typing import Callable, Dict, List
from modules.events.event import Event


EventHandler = Callable[[Event], None]


class EventBus:
    def __init__(self):
        self._subscribers = {}

    def subscribe(self, event_type: str, handler):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def emit(self, event):
        handlers = self._subscribers.get(event.type, [])
        for handler in handlers:
            handler(event)


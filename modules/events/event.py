from dataclasses import dataclass
from typing import Dict, Any


@dataclass(frozen=True)
class Event:
    type: str
    payload: Dict[str, Any] | None = None

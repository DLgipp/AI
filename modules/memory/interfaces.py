from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class MessageStore(ABC):
    @abstractmethod
    def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        meta: Optional[Dict] = None
    ):
        pass

    @abstractmethod
    def load_recent(
        self,
        session_id: str,
        limit: int
    ) -> List[Dict]:
        pass


class SessionStateStore(ABC):
    @abstractmethod
    def set(self, session_id: str, key: str, value: str):
        pass

    @abstractmethod
    def get(self, session_id: str, key: str) -> Optional[str]:
        pass

    @abstractmethod
    def get_all(self, session_id: str) -> Dict[str, str]:
        pass

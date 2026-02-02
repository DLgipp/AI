import json
from typing import List, Dict, Optional
from .db import get_connection
from .interfaces import MessageStore
from config import MEMORY_DB_PATH

class SQLiteMessageStore(MessageStore):
    def __init__(self, db_path=MEMORY_DB_PATH):
        self.db_path = db_path

    def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        meta: Optional[Dict] = None
    ):
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO messages (session_id, role, content, meta)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, role, content, json.dumps(meta) if meta else None)
            )
            conn.commit()

    def load_recent(self, session_id: str, limit: int) -> List[Dict]:
        with get_connection() as conn:
            cur = conn.execute(
                """
                SELECT role, content
                FROM messages
                WHERE session_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (session_id, limit)
            )

            rows = cur.fetchall()

        return [
            {"role": role, "content": content}
            for role, content in reversed(rows)
        ]

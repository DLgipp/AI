from typing import Dict, Optional
from .db import get_connection
from .interfaces import SessionStateStore


class SQLiteSessionStateStore(SessionStateStore):

    def set(self, session_id: str, key: str, value: str):
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO session_state (session_id, key, value)
                VALUES (?, ?, ?)
                ON CONFLICT(session_id, key)
                DO UPDATE SET value = excluded.value,
                              updated_at = CURRENT_TIMESTAMP
                """,
                (session_id, key, value)
            )
            conn.commit()

    def get(self, session_id: str, key: str) -> Optional[str]:
        with get_connection() as conn:
            cur = conn.execute(
                """
                SELECT value FROM session_state
                WHERE session_id = ? AND key = ?
                """,
                (session_id, key)
            )
            row = cur.fetchone()
            return row[0] if row else None

    def get_all(self, session_id: str) -> Dict[str, str]:
        with get_connection() as conn:
            cur = conn.execute(
                """
                SELECT key, value FROM session_state
                WHERE session_id = ?
                """,
                (session_id,)
            )
            return dict(cur.fetchall())

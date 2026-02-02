import sqlite3
from pathlib import Path

DB_PATH = Path("data/memory.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    with get_connection() as conn:
        cur = conn.cursor()

        # История диалогов (сырая)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role TEXT,
            content TEXT,
            meta TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Сессионное состояние
        cur.execute("""
        CREATE TABLE IF NOT EXISTS session_state (
            session_id TEXT,
            key TEXT,
            value TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (session_id, key)
        )
        """)

        conn.commit()

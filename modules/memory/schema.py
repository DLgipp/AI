import sqlite3

def init_db(db_path: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Основные сообщения диалога
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        meta TEXT
    )
    """)

    # Сессионное состояние
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS session_state (
        session_id TEXT NOT NULL,
        key TEXT NOT NULL,
        value TEXT,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (session_id, key)
    )
    """)

    # Задел под долгосрочную / важную память
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS memory_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        type TEXT,
        content TEXT,
        importance INTEGER DEFAULT 0,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

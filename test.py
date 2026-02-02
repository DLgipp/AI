from modules.memory.message_store import SQLiteMessageStore

store = SQLiteMessageStore()

session_id = "test_session"

# Сохраняем сообщение
store.save_message(session_id, "user", "Привет!", {"emotion": "happy"})

# Загружаем последние 5 сообщений
msgs = store.load_recent(session_id, limit=5)
print(msgs)

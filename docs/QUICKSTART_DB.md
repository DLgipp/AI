# 🚀 Quick Start - Production Databases

## 1. Установка зависимостей

```bash
cd c:\AI
venv\Scripts\activate
pip install -r requirements.txt
```

---

## 2. Запуск баз данных

```bash
docker-compose -f docker-compose.databases.yml up -d
```

**Проверка:**
```bash
docker-compose -f docker-compose.databases.yml ps
```

Должны быть запущены:
- `ai_postgres` (PostgreSQL)
- `ai_milvus` (Milvus)
- `ai_etcd` (Milvus dependency)
- `ai_minio` (Milvus dependency)
- `ai_neo4j` (Neo4j)

---

## 3. Тестирование подключения

```bash
python scripts/test_database_connections.py
```

**Ожидаемый результат:**
```
✅ PostgreSQL: ALL TESTS PASSED
✅ Milvus: ALL TESTS PASSED
✅ Neo4j: ALL TESTS PASSED
✅ Memory Layer: ALL TESTS PASSED

Total: 4/4 tests passed
🎉 All databases are ready for production use!
```

---

## 4. Миграция данных (если нужно)

Если у вас есть данные в SQLite и вы хотите их перенести:

```bash
python scripts/migrate_databases.py
```

---

## 5. Запуск приложения

```bash
python main.py
```

---

## 🔧 Доступ к базам данных

### PostgreSQL

```bash
# CLI
psql -U postgres -d ai_assistant

# Или через pgAdmin
# Подключение: localhost:5432
```

### Milvus

```python
# Через Python
from pymilvus import connections
connections.connect(host="localhost", port=19530)
```

### Neo4j

```
# Откройте в браузере: http://localhost:7474
# Login: neo4j
# Password: password
```

---

## 🛑 Остановка баз данных

```bash
docker-compose -f docker-compose.databases.yml down
```

**С удалением данных (осторожно!):**
```bash
docker-compose -f docker-compose.databases.yml down -v
```

---

## 📊 Проверка статистики

```python
from modules.memory import MemoryLayer

memory = MemoryLayer(use_production_dbs=True)

# Получить статистику всех баз
stats = memory.get_statistics()
print(stats)

# Закрыть подключения
memory.episodic.close()
memory.semantic.close()
memory.relational.close()
memory.personality.close()
```

---

## ⚠️ Возможные проблемы

### PostgreSQL не подключается

```bash
# Проверить логи
docker-compose -f docker-compose.databases.yml logs postgres

# Перезапустить
docker-compose -f docker-compose.databases.yml restart postgres
```

### Milvus не подключается

```bash
# Milvus требует etcd и minio
docker-compose -f docker-compose.databases.yml up -d milvus-standalone etcd minio

# Проверить логи
docker-compose -f docker-compose.databases.yml logs milvus-standalone
```

### Neo4j не подключается

```bash
# Проверить статус
docker-compose -f docker-compose.databases.yml ps neo4j

# Neo4j Browser: http://localhost:7474
```

---

## 📚 Документация

- `docs/DATABASE_SETUP.md` - Полная инструкция по настройке
- `docs/DATABASE_CHANGES.md` - Описание изменений
- `docs/DATABASE_MIGRATION_SUMMARY.md` - Детали миграции

---

## ✅ Готово!

Теперь ваше приложение использует production базы данных:
- PostgreSQL для эпизодической и личностной памяти
- Milvus для семантической памяти (векторный поиск)
- Neo4j для реляционной памяти (графовые связи)

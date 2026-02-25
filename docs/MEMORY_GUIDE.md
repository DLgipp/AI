# 📚 Полная документация по работе с памятью

## 🎯 Обзор

Система памяти эволюционирующего ИИ-ассистента состоит из 4 уровней и предоставляет инструменты для просмотра и анализа.

---

## 🗂 Типы памяти

### 1. Эпизодическая память
**Файл:** `data/episodic_memory.db`

**Хранит:**
- ✅ Разговоры (user/assistant сообщения)
- ✅ Эмоции (валентность, возбуждение)
- ✅ Важность событий
- ✅ Темы и намерения
- ✅ Реакции пользователей (для RL)

**Просмотр:**
```bash
python memory_inspector.py --eps 10
```

### 2. Семантическая память
**Файл:** `data/semantic_memory.db`

**Хранит:**
- ✅ Концепты и знания
- ✅ Векторные эмбеддинги
- ✅ Категории и теги
- ✅ Важность знаний

**Просмотр:**
```bash
python memory_inspector.py --sem 10
```

### 3. Реляционная память
**Файл:** `data/relational_memory.db`

**Хранит:**
- ✅ Сущности (entities)
- ✅ Связи между сущностями
- ✅ Силу связей
- ✅ Типы отношений

**Просмотр:**
```bash
python memory_inspector.py  # затем: rel [имя_сущности]
```

### 4. Личностная память
**Файл:** `data/personality_memory.db`

**Хранит:**
- ✅ 10 черт личности (Big Five + 5)
- ✅ 8 ценностей с весами
- ✅ Текущее настроение
- ✅ Отношения с пользователями
- ✅ Историю версий

**Просмотр:**
```bash
python memory_inspector.py --per
```

---

## 🛠 Инструменты

### 1. Memory Inspector (отдельный скрипт)

**Полнофункциональный инструмент для работы с памятью.**

#### Быстрый старт

```bash
cd c:\AI
venv\Scripts\activate

# Статистика
python memory_inspector.py --stats

# Эпизодическая память
python memory_inspector.py --eps 10

# Личность
python memory_inspector.py --per

# Интерактивный режим
python memory_inspector.py
```

#### Интерактивные команды

| Команда | Описание |
|---------|----------|
| `stats` | Общая статистика |
| `eps [N]` | Эпизодическая (N записей) |
| `sem [N]` | Семантическая (N концептов) |
| `rel [name]` | Реляционная (связи сущности) |
| `per` | Личность |
| `search QUERY` | Поиск |
| `export [file]` | Экспорт в JSON |
| `quit` | Выход |

#### Пример сессии

```
$ python memory_inspector.py

============================================================
🔍 MEMORY INSPECTOR
============================================================

Команды:
  stats          - общая статистика
  eps [N]        - эпизодическая
  sem [N]        - семантическая
  rel [name]     - реляционная
  per            - личность
  search QUERY   - поиск
  export [file]  - экспорт
  quit           - выход
============================================================

memory> stats
... (вывод статистики) ...

memory> per
... (вывод личности) ...

memory> eps 5
... (последние 5 записей) ...

memory> search ИИ
... (поиск по памяти) ...

memory> export backup.json
✅ Память экспортирована в backup.json

memory> quit
👋 До свидания!
```

---

### 2. Python API

```python
from modules.memory import MemoryLayer

# Создание доступа к памяти
memory = MemoryLayer()

# Эпизодическая
recent = memory.episodic.get_recent(session_id="default", limit=10)
by_topic = memory.episodic.get_by_topic("programming", limit=5)
emotional = memory.episodic.get_emotional_memories(min_intensity=0.7)

# Семантическая
by_concept = memory.semantic.get_by_concept("ИИ", limit=5)
by_vector = memory.semantic.search_by_vector(embedding, limit=5)

# Реляционная
connections = memory.relational.get_entity_connections("ИИ", max_depth=2)
path = memory.relational.find_path("ИИ", "программирование")

# Личность
state = memory.personality.get_state()
print(f"Доминирующая черта: {state.get_dominant_trait()}")
print(f"Настроение: {state.mood_valence:+.2f}")
```

---

### 3. Cognitive Pipeline API

```python
from modules.cognitive_pipeline import CognitivePipeline

pipeline = CognitivePipeline()

# Статистика сессии
stats = pipeline.get_statistics()
print(f"Воспоминаний: {stats['memory']['episodic']['total_memories']}")

# Поиск в памяти
context = pipeline.memory.get_context(session_id="default")
knowledge = pipeline.search_knowledge("программирование")

# Экспорт через инспектор
from memory_inspector import MemoryInspector
inspector = MemoryInspector()
inspector.show_statistics()
inspector.export_memory("session_export.json")
```

---

## 📊 Анализ памяти

### Проверка эмоций

```bash
python memory_inspector.py
memory> eps 20
```

Смотрите на колонку "Эмоция":
- `+0.5...+1.0` - положительные (😊)
- `-0.3...+0.3` - нейтральные (😐)
- `-1.0...-0.3` - отрицательные (😢)

### Проверка эволюции личности

```bash
# До сессии
python memory_inspector.py --per > before.txt

# ... сессия ...

# После сессии
python memory_inspector.py --per > after.txt

# Сравнить файлы
```

### Поиск проблем

**Пустые ответы LLM:**
```bash
memory> eps 10
# Проверить что сохранилось в content
```

**Неправильные эмоции:**
```bash
memory> search грустно
# Проверить emotion_valence
```

**Конфликты в памяти:**
```bash
memory> search конфликт
# Проверить когнитивные конфликты
```

---

## 💾 Экспорт и резервное копирование

### Экспорт в JSON

```bash
python memory_inspector.py
memory> export full_backup.json
```

**Структура файла:**
```json
{
  "exported_at": "2025-02-25T22:00:00",
  "episodic": [...],
  "semantic": [...],
  "relational": {...},
  "personality": {...}
}
```

### Импорт (в будущем)

```python
import json

with open("backup.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Восстановление (требует реализации)
# memory.restore_from_dict(data)
```

### Автоматический бэкап

```bash
# В crontab или Task Scheduler
python memory_inspector.py
memory> export backup_$(date +%Y%m%d).json
```

---

## 🔧 Отладка

### Проблема: "Database locked"

**Причина:** main.py использует базы данных.

**Решение:**
```bash
# 1. Остановить main.py (Ctrl+C)
# 2. Запустить инспектор
python memory_inspector.py
```

### Проблема: "No memories found"

**Причина:** Базы пустые или не в той папке.

**Решение:**
```bash
# Проверить базы
dir data\*.db

# Если нет - запустить ассистента
python main.py
# Говорить с ним для создания воспоминаний
```

### Проблема: "Unicode error"

**Решение для Windows:**
```bash
chcp 65001
python memory_inspector.py
```

---

## 📈 Мониторинг

### Статистика для мониторинга

```bash
python memory_inspector.py --stats
```

**Ключевые метрики:**

| Метрика | Норма | Тревога |
|---------|-------|---------|
| Эпизодических записей | >10 | <5 |
| Средняя валентность | -0.3...+0.3 | <-0.5 или >+0.5 |
| Средняя важность | 0.4...0.7 | <0.3 или >0.8 |
| Версия личности | растёт | не меняется |

### Тренды

```bash
# Сохранять статистику ежедневно
python memory_inspector.py --stats >> daily_stats.log
```

**Анализ:**
- Рост эпизодической памяти = активные разговоры
- Изменение валентности = настроение пользователя
- Эволюция черт = обучение личности

---

## 🎓 Лучшие практики

### 1. Регулярная проверка

```bash
# Раз в день
python memory_inspector.py --stats

# Раз в неделю
python memory_inspector.py --per

# Раз в месяц
python memory_inspector.py
memory> export monthly_backup.json
```

### 2. Анализ сессий

```bash
# До сессии
memory> eps 0  # запомнить текущее количество

# После сессии
memory> eps 10  # проверить новые записи
memory> per     # проверить изменения личности
```

### 3. Поиск проблем

```bash
# Если LLM не отвечает
memory> eps 5  # проверить что сохранилось

# Если странные эмоции
memory> search грустно  # найти источник

# Если личность не эволюционирует
memory> per  # проверить версию
```

---

## 📚 Документы

- [MEMORY_INSPECTOR_GUIDE.md](MEMORY_INSPECTOR_GUIDE.md) - полное руководство
- [ARCHITECTURE.md](ARCHITECTURE.md) - архитектура памяти
- [README.md](README.md) - общее описание проекта

---

## 🆘 Поддержка

При проблемах:
1. Проверьте логи в `logs/`
2. Используйте `memory_inspector.py` для диагностики
3. Экспортируйте память для анализа

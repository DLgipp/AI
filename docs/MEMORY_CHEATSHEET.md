# 📝 Шпаргалка по памяти

## 🚀 Быстрые команды

### Просмотр памяти

```bash
cd c:\AI
venv\Scripts\activate

# Статистика всех типов
python memory_inspector.py --stats

# Эпизодическая (последние 10 записей)
python memory_inspector.py --eps 10

# Личность
python memory_inspector.py --per

# Интерактивный режим
python memory_inspector.py
```

### В интерактивном режиме

```
memory> stats          # Статистика
memory> eps 20         # 20 записей разговоров
memory> sem 15         # 15 концептов
memory> rel ИИ         # Связи сущности "ИИ"
memory> per            # Личность (черты, ценности)
memory> поиск запрос   # Поиск по памяти
memory> export backup  # Экспорт в JSON
memory> quit           # Выход
```

---

## 📊 Что где смотреть

### 🎯 LLM не отвечает

```bash
memory> eps 5
```
→ Проверить что сохранилось в `content`

### 😊 Проверить эмоции

```bash
memory> eps 10
```
→ Смотреть колонку "Эмоция" (valence)

### 👤 Проверить личность

```bash
memory> per
```
→ Черты, ценности, настроение

### 🔍 Найти информацию

```bash
memory> search программирование
```
→ Поиск по всем типам памяти

### 💾 Сделать бэкап

```bash
memory> export session_backup.json
```

---

## 📁 Файлы памяти

```
data/
├── episodic_memory.db      # Разговоры, события
├── semantic_memory.db      # Знания, концепты
├── relational_memory.db    # Связи между сущностями
└── personality_memory.db   # Личность, черты, ценности
```

---

## 🐛 Частые проблемы

### "Database locked"
→ Закрыть `main.py` (Ctrl+C)

### "No memories found"
→ Запустить `main.py` и поговорить с ассистентом

### Unicode символы
→ `chcp 65001` перед запуском

---

## 📈 Мониторинг

```bash
# Ежедневная статистика
python memory_inspector.py --stats >> daily.log

# Еженедельный бэкап
python memory_inspector.py
memory> export weekly_$(date).json
```

---

## 🔗 Документация

- [MEMORY_INSPECTOR_GUIDE.md](MEMORY_INSPECTOR_GUIDE.md) - подробно
- [MEMORY_GUIDE.md](MEMORY_GUIDE.md) - полное руководство
- [ARCHITECTURE.md](ARCHITECTURE.md) - архитектура

# Эволюционирующий ИИ-ассистент с личностью

Модульная архитектура для создания ИИ-ассистента с динамической личностью, способной к развитию через обучение с подкреплением.

## 📋 Содержание

- [О проекте](#о-проекте)
- [Что было реализовано](#что-было-реализовано)
- [Архитектура](#архитектура)
- [Быстрый старт](#быстрый-старт)
- [Структура проекта](#структура-проекта)
- [Конфигурация](#конфигурация)
- [Примеры использования](#примеры-использования)
- [Тестирование](#тестирование)
- [Расширение функциональности](#расширение-функциональности)

---

## 🎯 О проекте

Этот проект представляет собой **полную переработку архитектуры ИИ-ассистента** с добавлением следующих ключевых возможностей:

1. **Динамическая личность** — 10 черт личности (Big Five + дополнительные), система ценностей, настроение
2. **Многоуровневая память** — эпизодическая, семантическая, реляционная, личностная
3. **Эмоциональный интеллект** — распознавание эмоций, эмпатия, эмоциональная выразительность
4. **Обучение с подкреплением** — эволюция личности на основе обратной связи
5. **Контекстное понимание** — распознавание намерений, целей, тем, важности

### Ключевые отличия от оригинальной версии

| Было | Стало |
|------|-------|
| Статичная персона (MARIN_PERSONA) | Динамическая личность с 10 чертами |
| Плоская память (SQLite) | 4 уровня памяти (эпизодическая, семантическая, реляционная, личностная) |
| Прямая генерация ответа | 9-уровневый когнитивный пайплайн |
| Нет обучения | RL-эволюция на основе обратной связи |
| Нет понимания контекста | Глубокая интерпретация (эмоции, намерения, цели, важность) |

---

## ✨ Что было реализовано

### 1. Perception Layer (Восприятие)
**Файлы:** `modules/perception/`

- ✅ **InputNormalizer** — нормализация текста, очистка от слов-паразитов
- ✅ **EmotionDetector** — 7 эмоций, валентность, возбуждение, доминирование
- ✅ **IntentDetector** — 10 типов намерений с уверенностью
- ✅ **PerceptionLayer** — единый интерфейс

### 2. Interpretation Layer (Понимание)
**Файлы:** `modules/interpretation/`

- ✅ **TopicDetector** — 9 категорий тем, векторные эмбеддинги
- ✅ **GoalExtractor** — 6 типов целей, приоритет, срочность
- ✅ **ImportanceScorer** — 6 факторов важности
- ✅ **InterpretationLayer** — единый интерфейс

### 3. Memory Layer (Память)
**Файлы:** `modules/memory/`

- ✅ **EpisodicMemoryStore** — события, разговоры, эмоциональная оценка
- ✅ **SemanticMemoryStore** — знания, концепты, векторный поиск
- ✅ **RelationalMemoryStore** — граф сущностей и связей
- ✅ **PersonalityMemoryStore** — черты, ценности, настроение, отношения
- ✅ **MemoryLayer** — единый интерфейс для всех хранилищ

### 4. Personality Engine (Личность)
**Файлы:** `modules/personality/`

- ✅ **PersonalityState** — 10 черт, 8 ценностей, настроение
- ✅ **PersonalityEngine** — расчёт позиции (stance), когнитивные конфликты
- ✅ **PersonalityLayer** — управление состоянием личности

**Черты личности:**
- Openness (открытость опыту)
- Conscientiousness (добросовестность)
- Extraversion (экстраверсия)
- Agreeableness (доброжелательность)
- Neuroticism (невротизм)
- Curiosity (любопытство)
- Creativity (креативность)
- Empathy (эмпатия)
- Humor (чувство юмора)
- Assertiveness (уверенность)

### 5. Decision Layer (Решения)
**Файлы:** `modules/decision/`

- ✅ **DecisionLayer** — выбор стратегии ответа
- ✅ **DecisionVector** — параметры ответа
- ✅ **10 стратегий** — от прямого ответа до эмоциональной поддержки
- ✅ **7 эмоциональных тонов**

### 6. Prompt Construction Layer (Промпты)
**Файлы:** `modules/prompt_builder/`

- ✅ **PromptBuilder** — построение промптов на основе stance
- ✅ **Системные промпты** — с состоянием личности
- ✅ **Контекстные промпты** — с памятью и историей

### 7. Behavior & Expression Layer (Поведение)
**Файлы:** `modules/behavior/`

- ✅ **BehaviorProcessor** — пост-обработка вывода LLM
- ✅ **Речевые маркеры** — по чертам личности
- ✅ **Корректировка стиля** — тон, формальность, эмпатия

### 8. Evolution Layer (Эволюция / RL)
**Файлы:** `modules/evolution/`

- ✅ **EvolutionLayer** — расчёт вознаграждения, эволюция черт
- ✅ **5 источников вознаграждения** — явная/неявная обратная связь, цели, согласованность, социальная связь
- ✅ **Стабильная эволюция** — защита от резких изменений

### 9. Cognitive Pipeline (Интеграция)
**Файлы:** `modules/cognitive_pipeline.py`

- ✅ **CognitivePipeline** — единый интерфейс ко всем уровням
- ✅ **process()** — обработка ввода
- ✅ **process_llm_response()** — обработка вывода LLM
- ✅ **process_user_feedback()** — обучение на обратной связи

---

## 🏗 Архитектура

```
┌─────────────────────────────────────────────────────────────────┐
│                    COGNITIVE PIPELINE                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐                    │
│  │PERCEPTION│──▶│INTERPRET.│──▶│ MEMORY   │                    │
│  └──────────┘   └──────────┘   └────┬─────┘                    │
│                                      │                          │
│                                      ▼                          │
│                               ┌──────────┐                      │
│                               │PERSONALITY│                     │
│                               └────┬─────┘                      │
│                                    │                            │
│                                    ▼                            │
│                               ┌──────────┐                      │
│                               │ DECISION │                      │
│                               └────┬─────┘                      │
│                                    │                            │
│                                    ▼                            │
│                               ┌──────────┐                      │
│                               │  PROMPT  │                      │
│                               └────┬─────┘                      │
│                                    │                            │
│         ┌──────────────────────────┘                            │
│         │                                                       │
│         ▼                                                       │
│  ┌──────────┐                                                   │
│  │   LLM    │                                                   │
│  └────┬─────┘                                                   │
│       │                                                         │
│       ▼                                                         │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐                    │
│  │ BEHAVIOR │──▶│ EVOLUTION│──▶│ FEEDBACK │                    │
│  └──────────┘   └──────────┘   └──────────┘                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

Подробное описание архитектуры см. в [ARCHITECTURE.md](ARCHITECTURE.md)

---

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Базовое использование

```python
from modules.cognitive_pipeline import CognitivePipeline

# Создание пайплайна
pipeline = CognitivePipeline(
    session_id="session_1",
    user_id="user_1",
    assistant_name="Акари"
)

# Обработка сообщения
result = await pipeline.process(
    text="Привет! Расскажи что-нибудь интересное",
    silence_duration=5.0
)

# Получение ответа от LLM
llm_response = await generate_from_llm(
    prompt=result["prompt"],
    system=result["system_prompt"]
)

# Пост-обработка
output = pipeline.process_llm_response(
    llm_response=llm_response,
    pipeline_result=result
)

print(output["text"])
```

### 3. Интеграция с существующим main.py

Для интеграции с вашим текущим `main.py`:

```python
# В main.py добавить:
from modules.cognitive_pipeline import CognitivePipeline

# В функции main() создать пайплайн:
cognitive_pipeline = CognitivePipeline(
    session_id="default",
    user_id="default"
)

# Заменить llm_handler на:
async def llm_handler(event, dialog, silence_timer, cognitive_pipeline):
    text = event.payload["text"]
    
    # Обработка через когнитивный пайплайн
    result = await cognitive_pipeline.process(
        text=text,
        silence_duration=silence_timer._last_activity
    )
    
    # Генерация ответа
    response = await generate_response_async(
        result["system_prompt"],
        result["prompt"],
        silence_timer
    )
    
    # Пост-обработка
    output = cognitive_pipeline.process_llm_response(
        llm_response=response,
        pipeline_result=result
    )
    
    dialog.push_assistant_message(output["text"])
```

---

## 📁 Структура проекта

```
c:\AI\
├── modules/
│   ├── perception/           # Уровень 1: Восприятие
│   │   ├── input_normalizer.py
│   │   ├── emotion_detector.py
│   │   ├── intent_detector.py
│   │   └── __init__.py
│   ├── interpretation/       # Уровень 2: Понимание
│   │   ├── topic_detector.py
│   │   ├── goal_extractor.py
│   │   ├── importance_scorer.py
│   │   └── __init__.py
│   ├── memory/               # Уровень 3: Память
│   │   ├── episodic_memory.py
│   │   ├── semantic_memory.py
│   │   ├── relational_memory.py
│   │   ├── personality_memory.py
│   │   └── __init__.py
│   ├── personality/          # Уровень 4: Личность
│   │   ├── personality_engine.py
│   │   └── __init__.py
│   ├── decision/             # Уровень 5: Решения
│   │   ├── decision_layer.py
│   │   └── __init__.py
│   ├── prompt_builder/       # Уровень 6: Промпты
│   │   ├── prompt_builder.py
│   │   └── __init__.py
│   ├── behavior/             # Уровень 8: Поведение
│   │   ├── behavior_processor.py
│   │   └── __init__.py
│   ├── evolution/            # Уровень 9: Эволюция
│   │   ├── evolution_layer.py
│   │   └── __init__.py
│   └── cognitive_pipeline.py # Главный пайплайн
├── tests/
│   ├── test_perception.py
│   ├── test_interpretation.py
│   ├── test_memory_personality.py
│   └── test_decision_evolution_behavior.py
├── data/                     # Базы данных (создаются автоматически)
│   ├── episodic_memory.db
│   ├── semantic_memory.db
│   ├── relational_memory.db
│   └── personality_memory.db
├── config.py                 # Конфигурация
├── requirements.txt          # Зависимости
├── ARCHITECTURE.md           # Документация архитектуры
└── README.md                 # Этот файл
```

---

## ⚙️ Конфигурация

### Настройка личности (`config.py`)

```python
# Черты личности (0.0 - 1.0)
PERSONALITY_TRAITS = {
    "openness": 0.6,          # Открытость опыту
    "conscientiousness": 0.5, # Добросовестность
    "extraversion": 0.7,      # Экстраверсия
    "agreeableness": 0.6,     # Доброжелательность
    "neuroticism": 0.3,       # Невротизм
    "curiosity": 0.7,         # Любопытство
    "creativity": 0.6,        # Креативность
    "empathy": 0.7,           # Эмпатия
    "humor": 0.6,             # Чувство юмора
    "assertiveness": 0.5      # Уверенность
}

# Ценности (0.0 - 1.0)
PERSONALITY_VALUES = {
    "honesty": 0.8,           # Честность
    "creativity": 0.6,        # Креативность
    "freedom": 0.7,           # Свобода
    "helpfulness": 0.9,       # Полезность
    "knowledge": 0.8,         # Знание
    "fun": 0.6,               # Веселье
    "efficiency": 0.5,        # Эффективность
    "tradition": 0.3          # Традиции
}

# Параметры эволюции
EVOLUTION_RATE = 0.05         # Скорость эволюции
EVOLUTION_THRESHOLD = 0.3     # Порог изменений
```

### Настройка памяти

```python
# Пути к базам данных
EPISODIC_MEMORY_PATH = "data/episodic_memory.db"
SEMANTIC_MEMORY_PATH = "data/semantic_memory.db"
RELATIONAL_MEMORY_PATH = "data/relational_memory.db"
PERSONALITY_MEMORY_PATH = "data/personality_memory.db"

# Настройки извлечения
RECENT_MEMORY_LIMIT = 10          # Количество последних воспоминаний
EMOTIONAL_MEMORY_THRESHOLD = 0.6  # Порог для эмоциональных воспоминаний
```

---

## 📖 Примеры использования

### 1. Обработка сообщения с эмоциями

```python
from modules.cognitive_pipeline import CognitivePipeline

pipeline = CognitivePipeline()

# Сообщение с эмоциональной окраской
result = await pipeline.process(
    text="Я так расстроен, ничего не получается!",
    voice_features={"energy": 0.3, "pitch_variance": 0.2}
)

# Проверка распознанной эмоции
print(result["interpretation"]["emotion_full"])
# {'valence': -0.6, 'sadness': 0.7, 'dominant_emotion': 'sadness'}

# Проверка стратегии
print(result["decision"]["strategy"])
# PROVIDE_SUPPORT

# Проверка тона
print(result["decision"]["emotional_tone"])
# EMPATHETIC
```

### 2. Обучение на обратной связи

```python
# После получения ответа от пользователя
feedback_result = pipeline.process_user_feedback(
    feedback="Спасибо, ты очень помог!",
    pipeline_result=previous_result
)

# Проверка вознаграждения
print(feedback_result["reward"]["value"])
# 0.8 (положительное)

# Проверка статистики обучения
print(feedback_result["statistics"])
# {'total_rewards': 15, 'average_reward': 0.45, ...}
```

### 3. Получение статистики

```python
# Статистика пайплайна
stats = pipeline.get_statistics()

print(f"Длительность сессии: {stats['conversation_duration']} сек")
print(f"Всего воспоминаний: {stats['memory']['episodic']['total_memories']}")
print(f"Доминирующая черта: {stats['personality']['dominant_trait']}")
print(f"Настроение: {stats['personality']['current_mood_valence']:+.2f}")
```

### 4. Поиск в памяти

```python
from modules.memory import MemoryLayer

memory = MemoryLayer()

# Поиск по теме
memories = memory.episodic.get_by_topic("ai_ml", limit=5)

# Поиск эмоциональных воспоминаний
emotional = memory.episodic.get_emotional_memories(min_intensity=0.7)

# Семантический поиск по вектору
results = memory.semantic.search_by_vector(
    query_embedding=[0.8, 0.2, 0.3, 0.7, 0.4],
    limit=5
)

# Получение связей сущности
connections = memory.relational.get_entity_connections("ИИ", max_depth=2)
```

---

## 🧪 Тестирование

### Запуск всех тестов

```bash
python -m pytest tests/ -v
```

### Запуск тестов по модулям

```bash
# Тесты восприятия
python -m unittest tests/test_perception.py

# Тесты интерпретации
python -m unittest tests/test_interpretation.py

# Тесты памяти и личности
python -m unittest tests/test_memory_personality.py

# Тесты решений, эволюции и поведения
python -m unittest tests/test_decision_evolution_behavior.py
```

### Пример теста

```python
from modules.perception import PerceptionLayer

layer = PerceptionLayer()

# Тест определения эмоции
result = layer.process("Я очень счастлив!")
assert result["emotion"]["joy"] > 0.5
assert result["emotion"]["dominant_emotion"] == "joy"

# Тест определения намерения
result = layer.process("Что такое ИИ?")
assert result["intent"]["intent"] == "query"
```

---

## 🔧 Расширение функциональности

### 1. Добавление новой черты личности

```python
# В config.py добавить:
PERSONALITY_TRAITS["optimism"] = 0.6

# В personality_memory.py добавить обработку:
def set_trait(self, trait_name, value):
    if trait_name == "optimism":
        self.optimism = value
    # ...

# В personality_engine.py добавить влияние:
TRAIT_INFLUENCES["optimism"] = {
    "emotion_tone": 0.3,
    "engagement_level": 0.2
}
```

### 2. Добавление новой эмоции

```python
# В emotion_detector.py добавить:
class EmotionState:
    trust: float = 0.0
    anticipation: float = 0.0

# Добавить в лексикон:
TRUST_WORDS = {"доверяю", "верю", "уверен", "надеюсь"}

# Обновить detect():
emotion.trust = self._detect_emotion_category(words, self.TRUST_WORDS)
```

### 3. Интеграция с внешней векторной БД

```python
# Для Milvus:
# pip install pymilvus

from pymilvus import connections, Collection

class MilvusSemanticMemory:
    def __init__(self, collection_name="semantic"):
        connections.connect()
        self.collection = Collection(collection_name)
    
    def search_by_vector(self, query_embedding, limit=5):
        self.collection.load()
        results = self.collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param={"metric_type": "COSINE"},
            limit=limit
        )
        return results
```

### 4. Добавление ML-модели для эмоций

```python
# pip install transformers rusentiment

from transformers import AutoTokenizer, AutoModelForSequenceClassification

class MLEmotionDetector:
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained("blanchefort/rubert-base-cased-sentiment")
        self.model = AutoModelForSequenceClassification.from_pretrained("blanchefort/rubert-base-cased-sentiment")
    
    def detect(self, text):
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True)
        outputs = self.model(**inputs)
        scores = torch.softmax(outputs.logits, dim=1)[0]
        return {
            "valence": scores[2].item() - scores[0].item(),  # positive - negative
            "arousal": max(scores).item()
        }
```

---

## 📊 Сравнение производительности

| Метрика | До | После |
|---------|-----|-------|
| Глубина понимания | Базовое | Глубокое (9 уровней) |
| Адаптивность | Статичная персона | Эволюционирующая личность |
| Контекст | Только история | 4 уровня памяти |
| Эмоциональность | Через промпт | Детекция + выражение |
| Обучение | Нет | RL с эволюцией |

---

## 🤝 Вклад в проект

### Что можно улучшить:

1. **ML-модели** — замена rule-based детекторов на нейросети
2. **Базы данных** — PostgreSQL, Milvus, Neo4j для продакшена
3. **Мультимодальность** — анализ изображений, экрана, жестов
4. **Долгосрочная память** — консолидация воспоминаний
5. **Социальное обучение** — обмен опытом между ассистентами

---

## 📝 Лицензия

Проект создан для образовательных и исследовательских целей.

---

## 📞 Контакты

Вопросы и предложения направляйте через Issues на GitHub.

---

## 🙏 Благодарности

Архитектура вдохновлена современными исследованиями в области:
- Когнитивной архитектуры
- Эмоционального ИИ
- Обучения с подкреплением
- Персонализированных ассистентов

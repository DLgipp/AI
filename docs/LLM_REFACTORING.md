# 🔄 Рефакторинг LLM: Вынос в отдельный модуль

## 📋 Что сделано

LLM логика вынесена из `main.py` в отдельный модуль `modules/llm/llm_service.py`.

---

## 🎯 Преимущества

### До рефакторинга

```python
# main.py
async def generate_llm_response(...):
    # Прямой вызов ollama.chat
    response = chat(model=MODEL_NAME, messages=...)
    # Логика обработки в main.py
    # Логирование в main.py
    # Обработка ошибок в main.py
```

**Проблемы:**
- ❌ Смешанная ответственность
- ❌ Сложно тестировать
- ❌ Дублирование кода
- ❌ Трудно заменить LLM провайдера

### После рефакторинга

```python
# main.py
async def generate_llm_response(...):
    # Вызов сервиса
    request = LLMRequest(...)
    response = llm_service.generate(request)
    return response.content
```

**Преимущества:**
- ✅ Разделение ответственности
- ✅ Легко тестировать (mock'и)
- ✅ Централизованная логика
- ✅ Простая замена провайдера

---

## 🏗 Архитектура

```
┌─────────────┐
│   main.py   │
└──────┬──────┘
       │ использует
       ↓
┌─────────────────┐
│  LLM Service    │  ← modules/llm/llm_service.py
│  (llm_service)  │
└──────┬──────────┘
       │ инкапсулирует
       ↓
┌─────────────┐
│   Ollama    │  ← внешний API
└─────────────┘
```

---

## 📦 Компоненты

### 1. LLMRequest

**Назначение:** Инкапсуляция параметров запроса.

```python
from modules.llm.llm_service import LLMRequest

request = LLMRequest(
    system_prompt="Ты Акари, ИИ-ассистент.",
    user_prompt="Привет!",
    history=[
        {"role": "user", "content": "Привет!"},
        {"role": "assistant", "content": "Привет! Как дела?"}
    ],
    temperature=0.7,
    max_tokens=150
)
```

### 2. LLMResponse

**Назначение:** Инкапсуляция ответа + метаданные.

```python
from modules.llm.llm_service import LLMResponse

response = LLMResponse(
    content="Привет! Чем могу помочь?",
    latency_ms=3185.4,
    tokens=50,
    model="gpt-oss:120b-cloud"
)

# Проверка успеха
if response.success:
    print(response.content)
else:
    print(f"Ошибка: {response.error}")
```

### 3. LLMService

**Назначение:** Основная логика работы с LLM.

```python
from modules.llm.llm_service import LLMService

service = LLMService(
    model_name="gpt-oss:120b-cloud",
    default_temperature=0.7,
    default_max_tokens=150
)

# Синхронный вызов
response = service.generate(request)

# Асинхронный вызов
response = await service.generate_async(request)

# Упрощённый вызов
text = service.generate_simple(
    system_prompt="Ты Акари.",
    user_prompt="Привет!"
)
```

---

## 🔧 Использование в main.py

### Импорт

```python
from modules.llm.llm_service import (
    LLMService,
    LLMRequest,
    get_llm_service
)
```

### Инициализация

```python
async def main():
    global llm_service
    
    # Инициализация сервиса
    llm_service = get_llm_service()
    
    # ... остальной код
```

### Генерация ответа

```python
async def generate_llm_response(...):
    global llm_service
    
    # Создание запроса
    request = LLMRequest(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        history=history_formatted
    )
    
    # Генерация через сервис
    response = llm_service.generate(request)
    
    return response.content
```

---

## 🧪 Тестирование

### Unit тест с mock

```python
import unittest
from unittest.mock import patch
from modules.llm.llm_service import LLMService, LLMRequest

class TestLLMService(unittest.TestCase):
    
    @patch('modules.llm.llm_service.chat')
    def test_generate_success(self, mock_chat):
        # Настройка мока
        mock_chat.return_value = {
            "message": {"content": "Привет!"},
            "eval_count": 10
        }
        
        # Тест
        service = LLMService()
        request = LLMRequest(
            system_prompt="Test",
            user_prompt="Hello"
        )
        response = service.generate(request)
        
        # Assertions
        self.assertTrue(response.success)
        self.assertEqual(response.content, "Привет!")
        self.assertEqual(response.tokens, 10)
    
    @patch('modules.llm.llm_service.chat')
    def test_generate_error(self, mock_chat):
        # Настройка мока с ошибкой
        mock_chat.side_effect = Exception("Connection error")
        
        # Тест
        service = LLMService()
        request = LLMRequest(...)
        response = service.generate(request)
        
        # Assertions
        self.assertFalse(response.success)
        self.assertIn("Connection error", response.error)
```

### Integration тест

```python
def test_real_llm_call():
    """Тест с реальным LLM (требует Ollama)."""
    service = LLMService()
    
    request = LLMRequest(
        system_prompt="Ты тестовый ассистент. Отвечай кратко.",
        user_prompt="Скажи 'OK'"
    )
    
    response = service.generate(request)
    
    assert response.success, f"LLM failed: {response.error}"
    assert len(response.content) > 0, "Empty response"
    assert response.latency_ms > 0, "No latency"
    print(f"✓ Response: {response.content[:50]}...")
    print(f"✓ Latency: {response.latency_ms:.1f} ms")
```

---

## 📊 Логирование

LLM Service автоматически логирует:

```python
# DEBUG
"LLM Service: 7 messages, system=445 chars"
"System prompt preview: You are Акари..."
"LLM response type: <class 'modules.llm.llm_service.LLMResponse'>"
"LLM content length: 142"

# PIPELINE
"LLM response: 3185.4 ms, 142 chars, 50 tokens"

# ERROR
"LLM error: Connection refused"
"LLM error from service: Timeout error"
```

---

## 🔄 Миграция старого кода

### Было (в main.py)

```python
from modules.llm.ollama_client import chat

async def generate_llm_response(...):
    messages = [
        {"role": "system", "content": system_prompt},
        *history,
        {"role": "user", "content": user_prompt}
    ]
    
    response = chat(
        model=MODEL_NAME,
        messages=messages,
        options={"temperature": 0.7}
    )
    
    content = response["message"]["content"]
    return content
```

### Стало

```python
from modules.llm.llm_service import LLMService, LLMRequest

llm_service = get_llm_service()

async def generate_llm_response(...):
    request = LLMRequest(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        history=history
    )
    
    response = llm_service.generate(request)
    return response.content
```

---

## 🛠 Расширение

### Добавление нового провайдера

```python
# modules/llm/openai_service.py
from modules.llm.llm_service import LLMService, LLMRequest, LLMResponse

class OpenAIService(LLMService):
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        self.api_key = api_key
        self.model = model
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key)
    
    def generate(self, request: LLMRequest) -> LLMResponse:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=request.to_messages()
        )
        
        return LLMResponse(
            content=response.choices[0].message.content,
            latency_ms=...,
            tokens=response.usage.total_tokens,
            model=self.model
        )
```

### Использование

```python
from modules.llm.openai_service import OpenAIService

openai = OpenAIService(api_key="sk-...")

request = LLMRequest(...)
response = openai.generate(request)
```

---

## 📈 Метрики

### Сбор статистики

```python
from modules.llm.llm_service import LLMService

service = LLMService()

# После запросов
print(f"Model: {service.model_name}")

# В response
response = service.generate(request)
print(f"Latency: {response.latency_ms:.1f} ms")
print(f"Tokens: {response.tokens}")
print(f"Content length: {len(response.content)}")
print(f"Success: {response.success}")
```

### Мониторинг

```python
# В main.py
from collections import defaultdict

llm_stats = defaultdict(int)

async def generate_llm_response(...):
    response = llm_service.generate(request)
    
    llm_stats["total"] += 1
    if response.success:
        llm_stats["success"] += 1
    else:
        llm_stats["errors"] += 1
    llm_stats["tokens"] += response.tokens
    
    return response.content

# Периодический вывод
print(f"LLM Stats: {dict(llm_stats)}")
```

---

## ✅ Чеклист

- [x] Создан `modules/llm/llm_service.py`
- [x] Созданы классы `LLMRequest`, `LLMResponse`, `LLMService`
- [x] Обновлён `main.py` для использования сервиса
- [x] Добавлена функция `get_llm_service()` (singleton)
- [x] Добавлено логирование
- [x] Добавлена обработка ошибок
- [x] Создана документация (`LLM_SERVICE_GUIDE.md`)
- [ ] Написаны unit тесты
- [ ] Написаны integration тесты

---

## 📚 Документация

- [LLM_SERVICE_GUIDE.md](LLM_SERVICE_GUIDE.md) - полное руководство
- [ARCHITECTURE.md](ARCHITECTURE.md) - общая архитектура
- [README.md](README.md) - описание проекта

---

## 🎯 Итог

**LLM логика теперь:**
- ✅ Инкапсулирована в отдельном модуле
- ✅ Легко тестируется (mock'и)
- ✅ Расширяема (новые провайдеры)
- ✅ Логируется централизованно
- ✅ Обрабатывает ошибки единообразно

**main.py стал:**
- ✅ Проще
- ✅ Чище
- ✅ Сфокусирован на основной логике

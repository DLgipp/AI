# 🤖 LLM Service Module

## 📋 Описание

Модуль `modules/llm/llm_service.py` инкапсулирует всю логику работы с языковой моделью (Ollama).

**Преимущества:**
- ✅ Разделение ответственности (Separation of Concerns)
- ✅ Упрощение тестирования
- ✅ Централизованная обработка ошибок
- ✅ Единая точка логирования
- ✅ Возможность замены LLM провайдера

---

## 🏗 Архитектура

```
main.py
    ↓
LLM Service (llm_service.py)
    ↓
Ollama API
```

**Компоненты:**

| Класс | Назначение |
|-------|------------|
| `LLMRequest` | Запрос к LLM (промпты, параметры) |
| `LLMResponse` | Ответ от LLM (контент, метаданные) |
| `LLMService` | Сервис для работы с LLM |

---

## 🚀 Быстрый старт

### Вариант 1: Использование сервиса

```python
from modules.llm.llm_service import LLMService, LLMRequest

# Создание сервиса
service = LLMService(model_name="gpt-oss:120b-cloud")

# Создание запроса
request = LLMRequest(
    system_prompt="Ты полезный ассистент.",
    user_prompt="Привет!",
    history=[]
)

# Генерация ответа
response = service.generate(request)

if response.success:
    print(response.content)
else:
    print(f"Ошибка: {response.error}")
```

### Вариант 2: Глобальный сервис

```python
from modules.llm.llm_service import get_llm_service

# Получение глобального сервиса
service = get_llm_service()

# Генерация
response = service.generate(request)
```

### Вариант 3: Быстрая функция

```python
from modules.llm.llm_service import generate_llm_response

# Простой вызов
text = generate_llm_response(
    system_prompt="Ты Акари, ИИ-ассистент.",
    user_prompt="Привет!",
    history=[]
)

print(text)
```

### Вариант 4: Асинхронная версия

```python
from modules.llm.llm_service import generate_llm_response_async

# Асинхронный вызов
text = await generate_llm_response_async(
    system_prompt="Ты Акари, ИИ-ассистент.",
    user_prompt="Привет!",
    history=[]
)
```

---

## 📖 API

### LLMRequest

```python
@dataclass
class LLMRequest:
    system_prompt: str       # Системный промпт
    user_prompt: str         # Пользовательский ввод
    history: List[Dict]      # История диалога
    temperature: float = 0.7 # Температура (0.0-1.0)
    max_tokens: int = 150    # Максимум токенов
    
    def to_messages(self) -> List[Dict[str, str]]:
        """Преобразовать в формат для Ollama."""
```

**Пример:**
```python
request = LLMRequest(
    system_prompt="Ты Акари, игривая и эмоциональная спутница.",
    user_prompt="Расскажи что-нибудь интересное",
    history=[
        {"role": "user", "content": "Привет!"},
        {"role": "assistant", "content": "Привет! Как дела?"}
    ],
    temperature=0.8,
    max_tokens=200
)
```

### LLMResponse

```python
@dataclass
class LLMResponse:
    content: str            # Текст ответа
    latency_ms: float       # Задержка в мс
    tokens: int = 0         # Количество токенов
    model: str = ""         # Модель
    error: Optional[str] = None  # Ошибка
    metadata: Dict = None   # Метаданные
    
    @property
    def success(self) -> bool:
        """Успешен ли запрос."""
```

**Использование:**
```python
response = service.generate(request)

if response.success:
    print(f"Ответ: {response.content}")
    print(f"Задержка: {response.latency_ms:.1f} мс")
    print(f"Токены: {response.tokens}")
else:
    print(f"Ошибка: {response.error}")
```

### LLMService

```python
class LLMService:
    def __init__(
        self,
        model_name: str = "gpt-oss:120b-cloud",
        default_temperature: float = 0.7,
        default_max_tokens: int = 150
    )
    
    def generate(request: LLMRequest) -> LLMResponse:
        """Синхронная генерация."""
    
    async def generate_async(request: LLMRequest) -> LLMResponse:
        """Асинхронная генерация."""
    
    def generate_simple(
        system_prompt: str,
        user_prompt: str,
        history: Optional[List[Dict]] = None
    ) -> str:
        """Упрощённый интерфейс."""
```

---

## 💡 Примеры использования

### 1. Базовый запрос

```python
from modules.llm.llm_service import LLMService, LLMRequest

service = LLMService()

request = LLMRequest(
    system_prompt="Ты полезный ассистент.",
    user_prompt="Что такое ИИ?"
)

response = service.generate(request)
print(response.content)
```

### 2. С историей диалога

```python
history = [
    {"role": "user", "content": "Привет!"},
    {"role": "assistant", "content": "Привет! Чем могу помочь?"},
    {"role": "user", "content": "Расскажи про себя."}
]

request = LLMRequest(
    system_prompt="Ты Акари, ИИ-ассистент.",
    user_prompt="Расскажи про себя.",
    history=history[:-1],  # Все кроме последнего
    temperature=0.8
)

response = service.generate(request)
```

### 3. Обработка ошибок

```python
response = service.generate(request)

if not response.success:
    if "connection" in response.error.lower():
        print("Проблема с подключением к Ollama")
    elif "timeout" in response.error.lower():
        print("Превышено время ожидания")
    else:
        print(f"Ошибка LLM: {response.error}")
```

### 4. Асинхронный вызов

```python
import asyncio
from modules.llm.llm_service import LLMService, LLMRequest

async def chat():
    service = LLMService()
    
    request = LLMRequest(
        system_prompt="Ты Акари.",
        user_prompt="Привет!"
    )
    
    response = await service.generate_async(request)
    print(response.content)

asyncio.run(chat())
```

### 5. В main.py

```python
# В main.py уже используется
from modules.llm.llm_service import LLMService, LLMRequest, get_llm_service

# Глобальный сервис
llm_service = get_llm_service()

# В llm_handler
request = LLMRequest(
    system_prompt=result.get("system_prompt", ""),
    user_prompt=text,
    history=history_formatted
)

response = llm_service.generate(request)
final_text = response.content
```

---

## 🔧 Конфигурация

### Через конструктор

```python
service = LLMService(
    model_name="llama3:8b",
    default_temperature=0.9,
    default_max_tokens=300
)
```

### Через config.py

```python
# config.py
MODEL_NAME = 'gpt-oss:120b-cloud'
MAX_TOKENS = 150

# В коде
from modules.llm.llm_service import get_llm_service
service = get_llm_service()  # Использует настройки из config
```

---

## 📊 Логирование

LLM Service автоматически логирует:

```python
# DEBUG уровень
"LLM: 7 messages, system=445 chars"
"System prompt preview: You are Акари..."

# PIPELINE уровень
"LLM response: 3185.4 ms, 142 chars, 50 tokens"

# ERROR уровень
"LLM error: Connection refused"
```

---

## 🧪 Тестирование

### Mock тест

```python
import unittest
from unittest.mock import Mock, patch
from modules.llm.llm_service import LLMService, LLMRequest

class TestLLMService(unittest.TestCase):
    
    @patch('modules.llm.llm_service.chat')
    def test_generate(self, mock_chat):
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
        
        # Проверка
        self.assertTrue(response.success)
        self.assertEqual(response.content, "Привет!")
```

### Интеграционный тест

```python
def test_real_llm():
    service = LLMService()
    
    request = LLMRequest(
        system_prompt="Ты тестовый ассистент.",
        user_prompt="Скажи 'OK'"
    )
    
    response = service.generate(request)
    
    assert response.success
    assert len(response.content) > 0
    assert response.latency_ms > 0
```

---

## 🛠 Расширение

### Добавление нового провайдера

```python
class OpenAIService(LLMService):
    def __init__(self, api_key: str):
        self.api_key = api_key
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key)
    
    def generate(self, request: LLMRequest) -> LLMResponse:
        # Реализация для OpenAI
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=request.to_messages()
        )
        
        return LLMResponse(
            content=response.choices[0].message.content,
            latency_ms=...,
            tokens=response.usage.total_tokens
        )
```

### Кэширование

```python
from functools import lru_cache

class CachedLLMService(LLMService):
    @lru_cache(maxsize=100)
    def generate_cached(self, request_hash: str) -> LLMResponse:
        # Кэшированная версия
        pass
    
    def generate(self, request: LLMRequest) -> LLMResponse:
        # Проверка кэша
        request_hash = hash(request.to_messages())
        
        if request_hash in self.cache:
            return self.cache[request_hash]
        
        response = super().generate(request)
        self.cache[request_hash] = response
        return response
```

---

## 📈 Метрики

### Для мониторинга

```python
response = service.generate(request)

# Метрики
print(f"Latency: {response.latency_ms:.1f} ms")
print(f"Tokens: {response.tokens}")
print(f"Content length: {len(response.content)}")
print(f"Success: {response.success}")
```

### Статистика

```python
from collections import defaultdict

class MonitoredLLMService(LLMService):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stats = defaultdict(int)
    
    def generate(self, request: LLMRequest) -> LLMResponse:
        self.stats["total_requests"] += 1
        
        response = super().generate(request)
        
        if response.success:
            self.stats["successful_requests"] += 1
        else:
            self.stats["failed_requests"] += 1
        
        self.stats["total_tokens"] += response.tokens
        
        return response
    
    def print_stats(self):
        print(f"Total: {self.stats['total_requests']}")
        print(f"Success: {self.stats['successful_requests']}")
        print(f"Failed: {self.stats['failed_requests']}")
        print(f"Total tokens: {self.stats['total_tokens']}")
```

---

## 📚 Связанные модули

- [cognitive_pipeline.py](cognitive_pipeline.py) - использует LLM Service
- [main.py](main.py) - инициализирует сервис
- [config.py](config.py) - настройки модели

---

## 🆘 Troubleshooting

### "Ollama not installed"

```bash
pip install ollama
```

### "Connection refused"

```bash
# Проверить что Ollama запущен
ollama list

# Перезапустить
ollama serve
```

### "Empty response"

```python
# Проверить промпт
print(f"System: {request.system_prompt[:100]}...")
print(f"User: {request.user_prompt}")

# Проверить модель
print(f"Model: {service.model_name}")
```

---

## ✅ Чеклист интеграции

- [ ] Импортировать `LLMService`, `LLMRequest`
- [ ] Создать сервис (`get_llm_service()` или новый)
- [ ] Создать запрос (`LLMRequest(...)`)
- [ ] Вызвать генерацию (`service.generate(request)`)
- [ ] Проверить ответ (`response.success`)
- [ ] Обработать ошибку (если есть)

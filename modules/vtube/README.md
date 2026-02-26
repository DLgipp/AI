# VTube Studio Module - Документация

Модуль для интеграции с VTube Studio API и управления VTuber-моделью на основе эмоций и состояний личности из когнитивного пайплайна.

## Обзор

```
┌─────────────────────────────────────────────────────────────────┐
│                    VTUBE STUDIO MODULE                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────┐         ┌──────────────────┐               │
│  │  VTubeController │         │ VTubeIntegration │               │
│  │                  │         │                  │               │
│  │  - WebSocket API │         │  - Эмоции        │               │
│  │  - Аутентификация│◀───────▶│  - Личность      │               │
│  │  - Параметры     │         │  - Blend         │               │
│  │  - Выражения     │         │                  │               │
│  └──────────────────┘         └──────────────────┘               │
│         │                            │                            │
│         │                            │                            │
│         ▼                            ▼                            │
│  ┌──────────────────────────────────────────────────┐            │
│  │            VTube Studio (WebSocket)              │            │
│  │              ws://localhost:8001                 │            │
│  └──────────────────────────────────────────────────┘            │
│                                                                   │
│         ▲                            ▲                            │
│         │                            │                            │
│  ┌──────────────────┐         ┌──────────────────┐               │
│  │ Perception Layer │         │ Personality Eng. │               │
│  │   (эмоции)       │         │  (состояния)     │               │
│  └──────────────────┘         └──────────────────┘               │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Быстрый старт

### 1. Прямое использование контроллера

```python
import asyncio
from modules.vtube import VTubeController, VTubeConfig

async def main():
    # Конфигурация
    config = VTubeConfig(
        websocket_url="ws://localhost:8001",
        plugin_name="My Plugin",
        plugin_developer="My Name"
    )
    
    # Контроллер
    controller = VTubeController(config)
    
    # Подключение
    await controller.connect()
    
    # Установка эмоции
    await controller.set_emotion('joy', intensity=0.8)
    
    # Перемещение модели
    await controller.move_model(x=0.1, y=-0.2, duration=0.5)
    
    # Инъекция параметров (lip-sync)
    await controller.inject_parameters({
        'MouthOpen': 0.5,
        'EyeOpenLeft': 0.9,
        'EyeOpenRight': 0.9
    })
    
    # Отключение
    await controller.disconnect()

asyncio.run(main())
```

### 2. Интеграция с когнитивным пайплайном

```python
from modules.vtube import VTubeIntegration

async def main():
    # Интеграция
    integration = VTubeIntegration()
    await integration.initialize()
    
    # После обработки эмоции в когнитивном пайплайне
    emotion_data = {
        'dominant_emotion': 'joy',
        'valence': 0.5,
        'arousal': 0.6,
        'joy': 0.7,
    }
    
    await integration.update_emotion(emotion_data)
    
    # После обновления состояния личности
    personality_state = {
        'engagement_level': 0.8,
        'extraversion': 0.7,
    }
    
    await integration.update_personality_state(personality_state)
    
    await integration.shutdown()
```

## API Контроллера

### VTubeController

#### Подключение

| Метод | Описание |
|-------|----------|
| `connect()` | Подключение к VTube Studio |
| `disconnect()` | Отключение |
| `reconnect()` | Переподключение |
| `is_connected` | Свойство: статус подключения |
| `is_authenticated` | Свойство: статус аутентификации |

#### Управление моделью

| Метод | Описание |
|-------|----------|
| `move_model(x, y, rotation, size, duration)` | Перемещение модели |
| `reset_model_position()` | Сброс позиции |
| `get_model_info()` | Информация о модели |

#### Эмоции

| Метод | Описание |
|-------|----------|
| `set_emotion(emotion, intensity, blend_time)` | Установка эмоции |
| `activate_expression(file, active, fade_time)` | Активация выражения |
| `get_expressions()` | Список выражений |

**Поддерживаемые эмоции:**
- `joy` - радость
- `sadness` - грусть
- `anger` - гнев
- `fear` - страх
- `surprise` - удивление
- `neutral` - нейтрально

#### Параметры

| Метод | Описание |
|-------|----------|
| `inject_parameters(parameters, face_found)` | Инъекция параметров |
| `get_statistics()` | Статистика VTS |
| `is_face_found()` | Статус лица |

#### Горячие клавиши

| Метод | Описание |
|-------|----------|
| `get_hotkeys(model_id)` | Список горячих клавиш |
| `trigger_hotkey(hotkey_id)` | Активация клавиши |

#### Предметы

| Метод | Описание |
|-------|----------|
| `load_item(file_name, ...)` | Загрузка предмета |
| `unload_item(instance_id)` | Выгрузка предмета |
| `get_items()` | Список предметов |

#### События

```python
controller.on("connected", callback)
controller.on("disconnected", callback)
controller.on("connection_lost", callback)
controller.on("model_loaded", callback)
```

## API Интеграции

### VTubeIntegration

Автоматически управляет эмоциями на основе данных из когнитивного пайплайна.

#### Методы

| Метод | Описание |
|-------|----------|
| `initialize()` | Инициализация |
| `shutdown()` | Завершение |
| `update_emotion(emotion_data)` | Обновление эмоции |
| `update_personality_state(state)` | Обновление личности |
| `set_expression(file, active)` | Прямая установка выражения |
| `move_model(...)` | Перемещение модели |
| `inject_face_parameters(params)` | Инъекция параметров |
| `trigger_hotkey(id)` | Горячая клавиша |

#### Свойства

| Свойство | Описание |
|----------|----------|
| `is_initialized` | Инициализирован ли |
| `is_connected` | Подключён ли |
| `controller` | Прямой доступ к контроллеру |
| `current_emotion` | Текущая эмоция |

## Конфигурация

### VTubeConfig

```python
from modules.vtube import VTubeConfig

config = VTubeConfig(
    # Подключение
    websocket_url="ws://localhost:8001",
    
    # Аутентификация
    plugin_name="Akari AI Assistant",
    plugin_developer="Akari Dev Team",
    plugin_icon_path=None,  # Путь к иконке 128x128
    auth_token_path="data/vtube_auth_token.json",
    
    # Переподключение
    reconnect_attempts=5,
    reconnect_delay=2.0,
    
    # Обновления
    parameter_update_interval=0.5,  # сек
    enable_face_tracking=True,
    enable_expressions=True,
    enable_items=True,
    
    # Позиция по умолчанию
    default_position_x=0.0,
    default_position_y=0.0,
    default_rotation=0.0,
    default_size=0.0,
    
    # Эмоции
    emotion_blend_time=0.3,  # сек
)
```

### Из config.py

```python
# VTUBE STUDIO CONFIGURATION
VTUBE_ENABLED = True
VTUBE_WEBSOCKET_URL = "ws://localhost:8001"
VTUBE_PLUGIN_NAME = "Akari AI Assistant"
VTUBE_PLUGIN_DEVELOPER = "Akari Dev Team"
VTUBE_AUTH_TOKEN_PATH = "data/vtube_auth_token.json"
VTUBE_RECONNECT_ATTEMPTS = 5
VTUBE_RECONNECT_DELAY = 2.0
VTUBE_PARAMETER_UPDATE_INTERVAL = 0.5
VTUBE_FACE_TRACKING_ENABLED = True
VTUBE_EXPRESSIONS_ENABLED = True
VTUBE_ITEMS_ENABLED = True
VTUBE_EMOTION_BLEND_TIME = 0.3
```

## Интеграция с основным процессом

### В main.py

```python
from modules.vtube import VTubeIntegration
from config import VTUBE_ENABLED

# Глобальное
vtube_integration: Optional[VTubeIntegration] = None

async def main():
    global vtube_integration
    
    # ... инициализация других компонентов ...
    
    # Инициализация VTube
    if VTUBE_ENABLED:
        vtube_integration = VTubeIntegration()
        if await vtube_integration.initialize():
            log("VTube Integration запущен")
        else:
            log("VTube Studio недоступен")
    
    # ... запуск циклов ...

async def llm_handler(event, dialog, silence_timer):
    global cognitive_pipeline, vtube_integration
    
    # Обработка через когнитивный пайплайн
    result = await cognitive_pipeline.process(text, ...)
    
    # Обновление эмоции в VTube
    if vtube_integration and vtube_integration.is_initialized:
        emotion = result.get('emotion', {})
        await vtube_integration.update_emotion(emotion)
        
        # Обновление состояния личности
        stance = result.get('stance', {})
        await vtube_integration.update_personality_state(stance)
    
    # ... генерация ответа ...
```

## Стандартные параметры VTube Studio

### Лицо

| Параметр | Мин | Макс | Описание |
|----------|-----|------|----------|
| `FaceAngleX` | -30 | 30 | Наклон влево/вправо |
| `FaceAngleY` | -30 | 30 | Наклон вверх/вниз |
| `FaceAngleZ` | -30 | 30 | Поворот |
| `FacePositionX` | -1 | 1 | Позиция X |
| `FacePositionY` | -1 | 1 | Позиция Y |

### Глаза

| Параметр | Мин | Макс | Описание |
|----------|-----|------|----------|
| `EyeOpenLeft` | 0 | 1 | Открыт левый глаз |
| `EyeOpenRight` | 0 | 1 | Открыт правый глаз |
| `EyeLookInLeft` | 0 | 1 | Взгляд внутрь (левый) |
| `EyeLookOutLeft` | 0 | 1 | Взгляд наружу (левый) |
| `EyeLookUpLeft` | 0 | 1 | Взгляд вверх (левый) |
| `EyeLookDownLeft` | 0 | 1 | Взгляд вниз (левый) |

### Рот

| Параметр | Мин | Макс | Описание |
|----------|-----|------|----------|
| `MouthOpen` | 0 | 1 | Открыт рот |
| `MouthSmileLeft` | 0 | 1 | Улыбка (левый) |
| `MouthSmileRight` | 0 | 1 | Улыбка (правый) |
| `MouthFrownLeft` | 0 | 1 | Гримаса (левый) |
| `MouthFrownRight` | 0 | 1 | Гримаса (правый) |

### Щёки и брови

| Параметр | Мин | Макс | Описание |
|----------|-----|------|----------|
| `CheekPuff` | 0 | 1 | Надутые щёки |
| `CheekSquintLeft` | 0 | 1 | Прищур щеки (левый) |
| `BrowInnerUp` | 0 | 1 | Бровь внутрь вверх |
| `BrowOuterUpLeft` | 0 | 1 | Бровь наружу вверх (левый) |
| `BrowDownLeft` | 0 | 1 | Бровь вниз (левый) |

## Маппинг эмоций

Эмоции из когнитивного пайплайна автоматически преобразуются в параметры VTube:

```python
EMOTION_PARAMETERS_MAP = {
    'joy': {
        'MouthSmileLeft': 1.0,
        'MouthSmileRight': 1.0,
        'EyeOpenLeft': 1.1,
        'EyeOpenRight': 1.1,
        'BrowOuterUpLeft': 0.3,
        'BrowOuterUpRight': 0.3,
        'CheekSquintLeft': 0.5,
        'CheekSquintRight': 0.5,
    },
    'sadness': {
        'MouthSmileLeft': -0.5,
        'MouthSmileRight': -0.5,
        'MouthFrownLeft': 0.7,
        'MouthFrownRight': 0.7,
        'BrowInnerUp': 0.6,
        'EyeOpenLeft': 0.8,
        'EyeOpenRight': 0.8,
    },
    # ... и т.д.
}
```

## Тестирование

### Запуск тестов

```bash
# pytest
python -m pytest modules/vtube/test_vtube.py -v

# Быстрый тест
python modules/vtube/test_vtube.py
```

### Требования

- VTube Studio запущен
- API включено (настройки → API → Включить API)
- Порт 8001 (или другой в настройках)

## Обработка ошибок

### Частые ошибки

| Код | Описание | Решение |
|-----|----------|---------|
| 50 | Пользователь отозвал доступ | Удалить токен, запросить заново |
| -1 | Нет соединения | Проверить запуск VTS |
| Таймаут | VTS не отвечает | Увеличить timeout |

### Пример

```python
try:
    await controller.connect()
except Exception as e:
    if "Connection refused" in str(e):
        print("VTube Studio не запущен")
    elif "authentication" in str(e).lower():
        print("Ошибка аутентификации")
```

## Советы

1. **Аутентификация:** Токен сохраняется автоматически при первой аутентификации
2. **Параметры:** Отправлять минимум раз в секунду, иначе контроль теряется
3. **Горячие клавиши:** Лимит - 1 раз в 5 кадров на клавишу
4. **Переподключение:** Автоматическое при потере соединения (до 5 попыток)
5. **Очистка:** Используйте `unloadWhenPluginDisconnects: true` для предметов

## Структура файлов

```
modules/vtube/
├── __init__.py          # Экспорт модуля
├── config.py            # Конфигурация
├── types.py             # Типы данных
├── controller.py        # Контроллер API
├── integration.py       # Интеграция с пайплайном
├── test_vtube.py        # Тесты
└── README.md            # Эта документация
```

## Зависимости

```
websockets>=10.0
```

Установка:
```bash
pip install websockets
```

## Примеры

### Lip-sync с аудио

```python
async def lip_sync(audio_amplitude: float):
    """Синхронизация губ с аудио."""
    await controller.inject_parameters({
        'MouthOpen': audio_amplitude * 0.8,
        'MouthSmileLeft': audio_amplitude * 0.2,
        'MouthSmileRight': audio_amplitude * 0.2,
        'FaceFound': True
    })
```

### Реакция на событие

```python
def on_user_interrupt():
    """Реакция на прерывание пользователя."""
    asyncio.create_task(controller.set_emotion(
        'surprise',
        intensity=0.9,
        blend_time=0.1
    ))
```

### Анимация приветствия

```python
async def greet_animation():
    """Анимация приветствия."""
    await controller.move_model(y=0.1, duration=0.3)
    await controller.set_emotion('joy', intensity=0.8)
    await asyncio.sleep(1.0)
    await controller.reset_model_position()
    await controller.set_emotion('neutral')
```

---

**Автор:** Акари AI Assistant  
**Версия:** 1.0.0  
**API VTube Studio:** 1.0

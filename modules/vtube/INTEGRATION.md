# Интеграция VTube Studio с основным приложением

## Быстрая интеграция в main.py

### Шаг 1: Импорт

```python
from modules.vtube import VTubeIntegration
from config import VTUBE_ENABLED
```

### Шаг 2: Инициализация

В функции `main()`:

```python
async def main():
    global vtube_integration
    
    # ... другая инициализация ...
    
    # Инициализация VTube Integration
    vtube_integration = None
    if VTUBE_ENABLED:
        vtube_integration = VTubeIntegration()
        if await vtube_integration.initialize():
            log("VTube Integration запущен", role="SYSTEM")
        else:
            log("VTube Studio недоступен", role="WARNING")
```

### Шаг 3: Обновление эмоций

В `llm_handler()` после обработки когнитивным пайплайном:

```python
async def llm_handler(event, dialog, silence_timer):
    global cognitive_pipeline, vtube_integration
    
    # Обработка через когнитивный пайплайн
    result = await cognitive_pipeline.process(text, ...)
    
    # Обновление VTube
    if vtube_integration and vtube_integration.is_initialized:
        # Эмоция из Perception Layer
        emotion = result.get('emotion', {})
        if emotion:
            await vtube_integration.update_emotion(emotion)
        
        # Состояние личности из Personality Engine
        stance = result.get('stance', {})
        if stance:
            personality_state = {
                'engagement_level': stance.get('engagement_level', 0.5),
                'emotion_tone': stance.get('emotion_tone', 0.5),
                'extraversion': stance.get('extraversion', 0.5),
            }
            await vtube_integration.update_personality_state(personality_state)
    
    # ... генерация ответа ...
```

### Шаг 4: Завершение

При завершении работы:

```python
async def shutdown():
    global vtube_integration
    
    if vtube_integration:
        await vtube_integration.shutdown()
```

## Полная схема

```
Пользователь говорит
    ↓
STT → Текст
    ↓
Cognitive Pipeline.process()
    ├── Perception Layer → Эмоция
    ├── Personality Layer → Состояние
    └── Decision Layer → Решение
    ↓
VTube Integration.update_emotion()
VTube Integration.update_personality_state()
    ↓
WebSocket → VTube Studio
    ↓
Анимация модели
    ↓
LLM генерирует ответ
    ↓
TTS произносит ответ
```

## Конфигурация

В `config.py` уже добавлены параметры:

```python
VTUBE_ENABLED = True
VTUBE_WEBSOCKET_URL = "ws://localhost:8001"
VTUBE_PLUGIN_NAME = "Akari AI Assistant"
VTUBE_PLUGIN_DEVELOPER = "Akari Dev Team"
# ... и другие
```

## Требования

1. **VTube Studio** должен быть запущен
2. **API включено** в настройках VTube Studio:
   - Настройки → API → Включить API
   - Порт: 8001 (по умолчанию)
3. **Установлен websockets**:
   ```bash
   pip install websockets
   ```

## Примечания

- Модуль работает **асинхронно** и не блокирует основной процесс
- **Автоматическое переподключение** при потере соединения (до 5 попыток)
- **Плавная интерполяция** эмоций (blend time 0.3 сек по умолчанию)
- Эмоции **затухают** до нейтральных при отсутствии обновлений

## Отладка

Если не работает:

1. Проверьте, что VTube Studio запущен
2. Проверьте, что API включено (порт 8001)
3. Запустите тест:
   ```bash
   python modules/vtube/test_vtube.py
   ```
4. Включите логирование:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

## Примеры использования

Смотрите `modules/vtube/example_usage.py` для подробных примеров:
- Базовое управление
- Интеграция с пайплайном
- Lip-sync
- Обработчики событий
- Горячие клавиши

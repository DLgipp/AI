"""
Пример использования VTube Studio Module

Демонстрация различных возможностей модуля для управления VTuber-моделью.
"""

import asyncio
import random
from modules.vtube import VTubeController, VTubeIntegration, VTubeConfig


# ==================== ПРИМЕР 1: Прямое управление контроллером ====================

async def example_basic_controller():
    """Базовый пример использования контроллера."""
    print("\n=== Пример 1: Базовое управление ===\n")
    
    config = VTubeConfig(
        plugin_name="Example Plugin",
        plugin_developer="Example Dev"
    )
    
    controller = VTubeController(config)
    
    try:
        # Подключение
        print("Подключение к VTube Studio...")
        if not await controller.connect():
            print("Не удалось подключиться к VTube Studio")
            return
        print("✓ Подключено\n")
        
        # Информация о модели
        model_info = await controller.get_model_info()
        if model_info:
            print(f"Модель: {model_info.model_name}")
            print(f"Загружена: {model_info.time_loaded:.1f} сек\n")
        
        # Тест эмоций
        print("Тест эмоций:")
        emotions = ['joy', 'sadness', 'anger', 'surprise', 'neutral']
        
        for emotion in emotions:
            print(f"  - {emotion}...")
            await controller.set_emotion(emotion, intensity=0.8)
            await asyncio.sleep(1.0)
        
        # Перемещение модели
        print("\nПеремещение модели:")
        positions = [
            (0.1, 0.0),
            (-0.1, 0.0),
            (0.0, 0.1),
            (0.0, -0.1),
            (0.0, 0.0),
        ]
        
        for x, y in positions:
            print(f"  - Позиция ({x}, {y})...")
            await controller.move_model(x=x, y=y, duration=0.3)
            await asyncio.sleep(0.5)
        
        # Статистика
        stats = await controller.get_statistics()
        if stats:
            print(f"\nСтатистика VTube Studio:")
            print(f"  Uptime: {stats.uptime:.1f} сек")
            print(f"  FPS: {stats.framerate:.1f}")
        
        print("\n✓ Пример завершён")
        
    finally:
        await controller.disconnect()
        print("\nОтключено от VTube Studio")


# ==================== ПРИМЕР 2: Интеграция с когнитивным пайплайном ====================

async def example_integration():
    """Пример интеграции с когнитивным пайплайном."""
    print("\n=== Пример 2: Интеграция с пайплайном ===\n")
    
    integration = VTubeIntegration()
    
    try:
        # Инициализация
        print("Инициализация интеграции...")
        if not await integration.initialize():
            print("Не удалось инициализировать интеграцию")
            return
        print("✓ Инициализировано\n")
        
        # Симуляция работы когнитивного пайплайна
        print("Симуляция эмоций из Perception Layer:")
        
        scenarios = [
            {
                'name': 'Радостное приветствие',
                'emotion': {
                    'dominant_emotion': 'joy',
                    'valence': 0.7,
                    'arousal': 0.8,
                    'joy': 0.9,
                    'surprise': 0.3,
                },
                'personality': {
                    'extraversion': 0.8,
                    'engagement_level': 0.9,
                }
            },
            {
                'name': 'Грустное сообщение',
                'emotion': {
                    'dominant_emotion': 'sadness',
                    'valence': -0.6,
                    'arousal': 0.3,
                    'sadness': 0.8,
                },
                'personality': {
                    'empathy': 0.9,
                    'emotion_tone': 0.4,
                }
            },
            {
                'name': 'Удивление',
                'emotion': {
                    'dominant_emotion': 'surprise',
                    'valence': 0.2,
                    'arousal': 0.9,
                    'surprise': 0.95,
                },
                'personality': {
                    'curiosity': 0.8,
                }
            },
            {
                'name': 'Спокойное состояние',
                'emotion': {
                    'dominant_emotion': 'neutral',
                    'valence': 0.0,
                    'arousal': 0.5,
                    'neutral': 0.8,
                },
                'personality': {}
            },
        ]
        
        for scenario in scenarios:
            print(f"Сценарий: {scenario['name']}")
            
            # Обновление эмоции
            await integration.update_emotion(scenario['emotion'])
            
            # Обновление личности
            if scenario.get('personality'):
                await integration.update_personality_state(scenario['personality'])
            
            # Ждём плавного перехода
            await asyncio.sleep(2.0)
        
        print("\n✓ Пример завершён")
        
    finally:
        await integration.shutdown()
        print("\nИнтеграция остановлена")


# ==================== ПРИМЕР 3: Lip-sync с аудио ====================

async def example_lipsync():
    """Пример lip-sync с симуляцией аудио."""
    print("\n=== Пример 3: Lip-sync ===\n")
    
    config = VTubeConfig()
    controller = VTubeController(config)
    
    try:
        if not await controller.connect():
            print("Не удалось подключиться")
            return
        
        print("Симуляция lip-sync...\n")
        
        # Симуляция аудио (амплитуда от 0 до 1)
        for i in range(50):
            # Генерируем "аудио" сигнал
            amplitude = random.random() * 0.8 + 0.2
            
            # Инъекция параметров для синхронизации губ
            await controller.inject_parameters({
                'MouthOpen': amplitude,
                'MouthSmileLeft': amplitude * 0.3,
                'MouthSmileRight': amplitude * 0.3,
                'CheekPuff': random.random() * 0.2,
                'FaceFound': True,
            }, face_found=True)
            
            # Эмулируем длительность фрейма аудио (30ms)
            await asyncio.sleep(0.03)
        
        # Очистка
        await controller.inject_parameters({}, face_found=False)
        
        print("\n✓ Lip-sync завершён")
        
    finally:
        await controller.disconnect()


# ==================== ПРИМЕР 4: Обработчики событий ====================

async def example_events():
    """Пример использования событий."""
    print("\n=== Пример 4: События ===\n")
    
    config = VTubeConfig()
    controller = VTubeController(config)
    
    # Определение обработчиков
    def on_connected():
        print("  [СОБЫТИЕ] Подключено к VTube Studio")
    
    def on_disconnected():
        print("  [СОБЫТИЕ] Отключено от VTube Studio")
    
    async def on_model_loaded(model_info):
        print(f"  [СОБЫТИЕ] Модель загружена: {model_info.model_name}")
    
    def on_connection_lost():
        print("  [СОБЫТИЕ] Соединение потеряно!")
    
    # Подписка на события
    controller.on("connected", on_connected)
    controller.on("disconnected", on_disconnected)
    controller.on("model_loaded", on_model_loaded)
    controller.on("connection_lost", on_connection_lost)
    
    try:
        if await controller.connect():
            print("\nЖдём события...\n")
            await asyncio.sleep(3.0)
        
    finally:
        await controller.disconnect()
        await asyncio.sleep(0.5)


# ==================== ПРИМЕР 5: Горячие клавиши ====================

async def example_hotkeys():
    """Пример использования горячих клавиш."""
    print("\n=== Пример 5: Горячие клавиши ===\n")
    
    config = VTubeConfig()
    controller = VTubeController(config)
    
    try:
        if not await controller.connect():
            print("Не удалось подключиться")
            return
        
        # Получение списка горячих клавиш
        hotkeys = await controller.get_hotkeys()
        
        if hotkeys:
            print(f"Найдено горячих клавиш: {len(hotkeys)}\n")
            
            for hk in hotkeys[:5]:  # Показываем первые 5
                print(f"  - {hk.name} (ID: {hk.hotkey_id})")
                print(f"    Тип: {hk.hotkey_type}")
                print(f"    Описание: {hk.description}\n")
            
            # Активация первой горячей клавиши (если есть)
            if hotkeys:
                print(f"Активация: {hotkeys[0].name}...")
                await controller.trigger_hotkey(hotkeys[0].hotkey_id)
                await asyncio.sleep(1.0)
        else:
            print("Горячие клавиши не найдены")
        
    finally:
        await controller.disconnect()


# ==================== ЗАПУСК ПРИМЕРОВ ====================

async def run_all_examples():
    """Запуск всех примеров."""
    print("="*60)
    print("VTube Studio Module - Примеры использования")
    print("="*60)
    
    examples = [
        ("Базовое управление", example_basic_controller),
        ("Интеграция с пайплайном", example_integration),
        ("Lip-sync", example_lipsync),
        ("События", example_events),
        ("Горячие клавиши", example_hotkeys),
    ]
    
    for name, example_func in examples:
        print(f"\n{'='*60}")
        print(f"Запуск примера: {name}")
        print(f"{'='*60}")
        
        try:
            await example_func()
        except Exception as e:
            print(f"Ошибка в примере '{name}': {e}")
        
        await asyncio.sleep(1.0)
    
    print("\n" + "="*60)
    print("Все примеры завершены")
    print("="*60)


if __name__ == "__main__":
    # Запуск всех примеров
    # asyncio.run(run_all_examples())
    
    # Или запуск конкретного примера:
    asyncio.run(example_basic_controller())
    # asyncio.run(example_integration())
    # asyncio.run(example_lipsync())
    # asyncio.run(example_events())
    # asyncio.run(example_hotkeys())

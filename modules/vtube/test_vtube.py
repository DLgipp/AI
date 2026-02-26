"""
Тесты для модуля VTube Studio

Запуск:
    python -m pytest modules/vtube/test_vtube.py -v

Или для быстрого теста:
    python modules/vtube/test_vtube.py
"""

import asyncio
import pytest
import sys
import os

# Добавляем корень проекта в path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from modules.vtube import VTubeController, VTubeConfig, VTubeIntegration
from modules.vtube.types import VTubeAuthStatus, EMOTION_PARAMETERS_MAP


# ==================== КОНФИГУРАЦИЯ ====================

@pytest.fixture
def vtube_config():
    """Конфигурация для тестов."""
    return VTubeConfig(
        websocket_url="ws://localhost:8001",
        plugin_name="Akari Test Plugin",
        plugin_developer="Akari Test",
        auth_token_path="data/vtube_test_auth_token.json",
        reconnect_attempts=2,
        reconnect_delay=1.0,
    )


@pytest.fixture
async def vtube_controller(vtube_config):
    """Контроллер для тестов."""
    controller = VTubeController(vtube_config)
    try:
        await controller.connect()
        yield controller
    finally:
        await controller.disconnect()


@pytest.fixture
async def vtube_integration(vtube_config):
    """Интеграция для тестов."""
    integration = VTubeIntegration(vtube_config)
    try:
        await integration.initialize()
        yield integration
    finally:
        await integration.shutdown()


# ==================== ТЕСТЫ ПОДКЛЮЧЕНИЯ ====================

class TestConnection:
    """Тесты подключения к VTube Studio."""
    
    @pytest.mark.asyncio
    async def test_connect(self, vtube_config):
        """Тест подключения."""
        controller = VTubeController(vtube_config)
        
        try:
            result = await controller.connect()
            
            # Если VTube Studio не запущен, тест пропускается
            if not result:
                pytest.skip("VTube Studio не запущен")
            
            assert controller.is_connected
            assert controller.is_authenticated
        finally:
            await controller.disconnect()
    
    @pytest.mark.asyncio
    async def test_auth_status(self, vtube_config):
        """Тест статуса аутентификации."""
        controller = VTubeController(vtube_config)
        
        assert controller.auth_status == VTubeAuthStatus.NOT_AUTHENTICATED
        
        try:
            await controller.connect()
            
            if controller.is_connected:
                assert controller.auth_status == VTubeAuthStatus.AUTHENTICATED
        finally:
            await controller.disconnect()
    
    @pytest.mark.asyncio
    async def test_reconnect(self, vtube_config):
        """Тест переподключения."""
        controller = VTubeController(vtube_config)
        
        try:
            await controller.connect()
            
            if not controller.is_connected:
                pytest.skip("VTube Studio не запущен")
            
            # Отключаем и подключаем снова
            await controller.disconnect()
            assert not controller.is_connected
            
            result = await controller.reconnect()
            
            if result:
                assert controller.is_connected
        finally:
            await controller.disconnect()


# ==================== ТЕСТЫ МОДЕЛИ ====================

class TestModel:
    """Тесты управления моделью."""
    
    @pytest.mark.asyncio
    async def test_get_model_info(self, vtube_controller):
        """Тест получения информации о модели."""
        if not vtube_controller.is_connected:
            pytest.skip("Нет подключения")
        
        model_info = await vtube_controller.get_model_info()
        
        if model_info:
            assert model_info.model_name
            assert model_info.model_id
    
    @pytest.mark.asyncio
    async def test_move_model(self, vtube_controller):
        """Тест перемещения модели."""
        if not vtube_controller.is_connected:
            pytest.skip("Нет подключения")
        
        # Перемещение
        await vtube_controller.move_model(
            x=0.1,
            y=-0.2,
            rotation=10,
            duration=0.3
        )
        
        # Возврат в исходную позицию
        await vtube_controller.reset_model_position()
    
    @pytest.mark.asyncio
    async def test_get_statistics(self, vtube_controller):
        """Тест получения статистики."""
        if not vtube_controller.is_connected:
            pytest.skip("Нет подключения")
        
        stats = await vtube_controller.get_statistics()
        
        if stats:
            assert stats.uptime >= 0
            assert stats.framerate >= 0


# ==================== ТЕСТЫ ЭМОЦИЙ ====================

class TestEmotions:
    """Тесты эмоций."""
    
    @pytest.mark.asyncio
    async def test_set_emotion_joy(self, vtube_controller):
        """Тест эмоции радости."""
        if not vtube_controller.is_connected:
            pytest.skip("Нет подключения")
        
        await vtube_controller.set_emotion('joy', intensity=0.8)
        await asyncio.sleep(0.5)
        await vtube_controller.set_emotion('neutral')
    
    @pytest.mark.asyncio
    async def test_set_emotion_all(self, vtube_controller):
        """Тест всех эмоций."""
        if not vtube_controller.is_connected:
            pytest.skip("Нет подключения")
        
        for emotion in EMOTION_PARAMETERS_MAP.keys():
            await vtube_controller.set_emotion(emotion, intensity=0.5)
            await asyncio.sleep(0.3)
        
        await vtube_controller.set_emotion('neutral')
    
    @pytest.mark.asyncio
    async def test_emotion_intensity(self, vtube_controller):
        """Тест интенсивности эмоции."""
        if not vtube_controller.is_connected:
            pytest.skip("Нет подключения")
        
        # Минимальная интенсивность
        await vtube_controller.set_emotion('joy', intensity=0.2)
        await asyncio.sleep(0.3)
        
        # Максимальная интенсивность
        await vtube_controller.set_emotion('joy', intensity=1.0)
        await asyncio.sleep(0.3)
        
        await vtube_controller.set_emotion('neutral')


# ==================== ТЕСТЫ ИНТЕГРАЦИИ ====================

class TestIntegration:
    """Тесты интеграции с когнитивным пайплайном."""
    
    @pytest.mark.asyncio
    async def test_initialize(self, vtube_config):
        """Тест инициализации интеграции."""
        integration = VTubeIntegration(vtube_config)
        
        try:
            result = await integration.initialize()
            
            if not result:
                pytest.skip("VTube Studio не запущен")
            
            assert integration.is_initialized
            assert integration.is_connected
        finally:
            await integration.shutdown()
    
    @pytest.mark.asyncio
    async def test_update_emotion(self, vtube_integration):
        """Тест обновления эмоции."""
        if not vtube_integration.is_initialized:
            pytest.skip("Интеграция не инициализирована")
        
        # Эмоция из perception layer
        emotion_data = {
            'dominant_emotion': 'joy',
            'valence': 0.5,
            'arousal': 0.6,
            'joy': 0.7,
            'sadness': 0.1,
            'anger': 0.0,
            'fear': 0.0,
            'surprise': 0.1,
            'neutral': 0.2,
        }
        
        await vtube_integration.update_emotion(emotion_data)
        await asyncio.sleep(0.5)
        
        # Проверка текущей эмоции
        current = vtube_integration.current_emotion
        if current:
            assert current.emotion == 'joy'
            assert 0 < current.intensity <= 1.0
    
    @pytest.mark.asyncio
    async def test_update_personality_state(self, vtube_integration):
        """Тест обновления состояния личности."""
        if not vtube_integration.is_initialized:
            pytest.skip("Интеграция не инициализирована")
        
        personality_state = {
            'engagement_level': 0.8,
            'emotion_tone': 0.4,
            'emotional_expression': 0.6,
            'extraversion': 0.7,
            'neuroticism': 0.3,
        }
        
        await vtube_integration.update_personality_state(personality_state)
    
    @pytest.mark.asyncio
    async def test_full_pipeline(self, vtube_integration):
        """Тест полного цикла: эмоция + личность."""
        if not vtube_integration.is_initialized:
            pytest.skip("Интеграция не инициализирована")
        
        # 1. Обновляем состояние личности
        await vtube_integration.update_personality_state({
            'extraversion': 0.8,
            'engagement_level': 0.9,
        })
        
        # 2. Обновляем эмоцию
        await vtube_integration.update_emotion({
            'dominant_emotion': 'surprise',
            'valence': 0.3,
            'arousal': 0.8,
            'surprise': 0.9,
        })
        
        # 3. Ждём обновления
        await asyncio.sleep(0.5)
        
        # 4. Сбрасываем
        await vtube_integration.update_emotion({
            'dominant_emotion': 'neutral',
            'valence': 0.0,
            'arousal': 0.5,
        })
        
        await asyncio.sleep(0.5)


# ==================== ТЕСТЫ ВЫРАЖЕНИЙ ====================

class TestExpressions:
    """Тесты выражений лица."""
    
    @pytest.mark.asyncio
    async def test_get_expressions(self, vtube_controller):
        """Тест получения списка выражений."""
        if not vtube_controller.is_connected:
            pytest.skip("Нет подключения")
        
        expressions = await vtube_controller.get_expressions()
        
        # Выражения могут отсутствовать
        if expressions:
            assert len(expressions) > 0
            assert expressions[0].name or expressions[0].file
    
    @pytest.mark.asyncio
    async def test_get_hotkeys(self, vtube_controller):
        """Тест получения горячих клавиш."""
        if not vtube_controller.is_connected:
            pytest.skip("Нет подключения")
        
        hotkeys = await vtube_controller.get_hotkeys()
        
        # Горячие клавиши могут отсутствовать
        if hotkeys:
            assert len(hotkeys) > 0
            assert hotkeys[0].hotkey_id


# ==================== ЗАПУСК ====================

if __name__ == "__main__":
    # Быстрый тест без pytest
    async def quick_test():
        print("=== VTube Studio Module Quick Test ===\n")
        
        config = VTubeConfig()
        controller = VTubeController(config)
        
        print("1. Подключение...")
        connected = await controller.connect()
        
        if not connected:
            print("   ✗ VTube Studio не запущен или недоступен")
            print("\nДля запуска тестов убедитесь, что:")
            print("  - VTube Studio запущен")
            print("  - API включено в настройках (порт 8001)")
            return
        
        print("   ✓ Подключено")
        
        print("\n2. Информация о модели...")
        model_info = await controller.get_model_info()
        if model_info:
            print(f"   ✓ Модель: {model_info.model_name}")
        else:
            print("   ✗ Модель не загружена")
        
        print("\n3. Тест эмоций...")
        for emotion in ['joy', 'surprise', 'neutral']:
            await controller.set_emotion(emotion, intensity=0.7)
            print(f"   ✓ Эмоция: {emotion}")
            await asyncio.sleep(0.5)
        
        print("\n4. Статистика...")
        stats = await controller.get_statistics()
        if stats:
            print(f"   ✓ Uptime: {stats.uptime:.1f}s, FPS: {stats.framerate:.1f}")
        
        print("\n5. Отключение...")
        await controller.disconnect()
        print("   ✓ Отключено")
        
        print("\n=== Тест завершён ===")
    
    asyncio.run(quick_test())

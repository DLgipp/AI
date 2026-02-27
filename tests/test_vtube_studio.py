"""
Тесты для модуля VTube Studio

Тестируются:
- VTubeStudioClient - подключение, аутентификация, управление параметрами
- VTubeIntegration - интеграция с когнитивным пайплайном
- Типы данных - ParameterValue, ColorTint, и т.д.

Для запуска тестов требуется запущенный VTube Studio с включенным API.
"""

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Добавляем путь к модулям
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.vtube_studio.vtube_client import (
    VTubeStudioClient,
    ParameterValue,
    ParameterMode,
    ParameterInfo,
    ExpressionConfig,
    ColorTint,
    ArtMeshMatcher,
    create_vtube_client
)

from modules.vtube_studio.integration import (
    VTubeIntegration,
    create_vtube_integration
)


# =============================================================================
# ТЕСТЫ ТИПОВ ДАННЫХ
# =============================================================================

class TestDataTypes(unittest.TestCase):
    """Тесты типов данных."""

    def test_parameter_value_to_dict(self):
        """Тест конвертации ParameterValue в dict."""
        pv = ParameterValue(id="FaceAngleX", value=10.5, weight=0.8)
        result = pv.to_dict()
        
        self.assertEqual(result["id"], "FaceAngleX")
        self.assertEqual(result["value"], 10.5)
        self.assertEqual(result["weight"], 0.8)
    
    def test_parameter_value_to_dict_no_weight(self):
        """Тест конвертации ParameterValue без веса."""
        pv = ParameterValue(id="EyeOpen", value=1.0)
        result = pv.to_dict()
        
        self.assertEqual(result["id"], "EyeOpen")
        self.assertEqual(result["value"], 1.0)
        self.assertNotIn("weight", result)
    
    def test_parameter_info_from_dict(self):
        """Тест создания ParameterInfo из dict."""
        data = {
            "name": "FaceAngleX",
            "value": 0.5,
            "min": -10.0,
            "max": 10.0,
            "default": 0.0
        }
        param = ParameterInfo.from_dict(data)
        
        self.assertEqual(param.name, "FaceAngleX")
        self.assertEqual(param.value, 0.5)
        self.assertEqual(param.min, -10.0)
        self.assertEqual(param.max, 10.0)
    
    def test_expression_config_to_dict(self):
        """Тест конвертации ExpressionConfig в dict."""
        config = ExpressionConfig(file="smile.exp3.json", active=True, fade_time=0.5)
        result = config.to_dict()
        
        self.assertEqual(result["expressionFile"], "smile.exp3.json")
        self.assertTrue(result["active"])
        self.assertEqual(result["fadeTime"], 0.5)
    
    def test_color_tint_to_dict(self):
        """Тест конвертации ColorTint в dict."""
        color = ColorTint(color_r=255, color_g=100, color_b=50, color_a=200)
        result = color.to_dict()
        
        self.assertEqual(result["colorR"], 255)
        self.assertEqual(result["colorG"], 100)
        self.assertEqual(result["colorB"], 50)
        self.assertEqual(result["colorA"], 200)
    
    def test_art_mesh_matcher_to_dict(self):
        """Тест конвертации ArtMeshMatcher в dict."""
        matcher = ArtMeshMatcher(
            tint_all=False,
            name_exact=["eye_left", "eye_right"],
            name_contains=["mouth"]
        )
        result = matcher.to_dict()
        
        self.assertFalse(result["tintAll"])
        self.assertEqual(result["nameExact"], ["eye_left", "eye_right"])
        self.assertEqual(result["nameContains"], ["mouth"])


# =============================================================================
# ТЕСТЫ VTUBE STUDIO CLIENT (MOCKED)
# =============================================================================

class TestVTubeStudioClientMocked(unittest.TestCase):
    """Тесты VTubeStudioClient с моками."""

    def setUp(self):
        """Настройка тестов."""
        self.client = VTubeStudioClient(
            plugin_name="Test Plugin",
            plugin_developer="Test Developer",
            ws_url="ws://localhost:8001"
        )
    
    def test_client_initialization(self):
        """Тест инициализации клиента."""
        self.assertEqual(self.client.plugin_name, "Test Plugin")
        self.assertEqual(self.client.plugin_developer, "Test Developer")
        self.assertEqual(self.client.ws_url, "ws://localhost:8001")
        self.assertFalse(self.client.is_connected)
        self.assertFalse(self.client.is_authenticated)
    
    def test_parameter_mode_enum(self):
        """Тест перечисления ParameterMode."""
        self.assertEqual(ParameterMode.SET.value, "set")
        self.assertEqual(ParameterMode.ADD.value, "add")
    
    @patch('modules.vtube_studio.vtube_client.websockets.connect', new_callable=AsyncMock)
    async def test_connect(self, mock_connect):
        """Тест подключения (с моком)."""
        mock_ws = AsyncMock()
        mock_ws.close = AsyncMock()
        mock_connect.return_value = mock_ws
        
        # Настраиваем mock для итерации
        mock_ws.__aiter__ = AsyncMock(return_value=iter([]))
        
        result = await self.client.connect()
        self.assertTrue(result)
        self.assertTrue(self.client.is_connected)
    
    def test_emotion_parameter_map(self):
        """Тест маппинга эмоций на параметры."""
        self.assertIn("joy", self.client.EMOTION_PARAMETER_MAP)
        self.assertIn("sadness", self.client.EMOTION_PARAMETER_MAP)
        self.assertIn("anger", self.client.EMOTION_PARAMETER_MAP)
        self.assertIn("fear", self.client.EMOTION_PARAMETER_MAP)
        self.assertIn("surprise", self.client.EMOTION_PARAMETER_MAP)
        self.assertIn("neutral", self.client.EMOTION_PARAMETER_MAP)
    
    def test_emotion_parameters_structure(self):
        """Тест структуры параметров эмоций."""
        for emotion, params in self.client.EMOTION_PARAMETER_MAP.items():
            self.assertIsInstance(params, dict)
            # Все эмоции должны иметь MouthOpen и EyeOpen
            self.assertIn("MouthOpen", params)
            self.assertIn("EyeOpen", params)


# =============================================================================
# ТЕСТЫ VTUBE INTEGRATION (MOCKED)
# =============================================================================

class TestVTubeIntegrationMocked(unittest.TestCase):
    """Тесты VTubeIntegration с моками."""

    def setUp(self):
        """Настройка тестов."""
        self.mock_client = AsyncMock(spec=VTubeStudioClient)
        self.mock_client.is_connected = False
        self.mock_client.is_authenticated = False
        
        self.integration = VTubeIntegration(
            client=self.mock_client,
            auto_connect=False
        )
    
    def test_integration_initialization(self):
        """Тест инициализации интеграции."""
        self.assertEqual(self.integration._emotion_smoothing, 0.3)
        self.assertEqual(self.integration._update_interval, 0.1)
        self.assertEqual(self.integration._frames_updated, 0)
        self.assertFalse(self.integration._running)
    
    def test_get_statistics(self):
        """Тест получения статистики."""
        stats = self.integration.get_statistics()
        
        self.assertIn("connected", stats)
        self.assertIn("current_emotions", stats)
        self.assertIn("target_emotions", stats)
        self.assertIn("frames_updated", stats)
    
    def test_emotion_smoothing_property(self):
        """Тест свойства сглаживания эмоций."""
        self.integration._emotion_smoothing = 0.5
        self.assertEqual(self.integration._emotion_smoothing, 0.5)
    
    @patch.object(VTubeIntegration, '_apply_emotions', new_callable=AsyncMock)
    def test_set_emotion_by_name_immediate(self, mock_apply):
        """Тест установки эмоции по имени (немедленно)."""
        async def run_test():
            await self.integration.set_emotion_by_name("joy", 0.8, immediate=True)
            
            self.assertEqual(self.integration._current_emotions["joy"], 0.8)
            mock_apply.assert_called_once()
        
        asyncio.run(run_test())
    
    def test_set_emotion_by_name_invalid(self):
        """Тест установки несуществующей эмоции."""
        async def run_test():
            await self.integration.set_emotion_by_name("invalid_emotion", 1.0)
            
            # Должна установиться neutral
            self.assertEqual(self.integration._target_emotions["neutral"], 1.0)
        
        asyncio.run(run_test())
    
    @patch.object(VTubeIntegration, '_apply_emotions', new_callable=AsyncMock)
    async def test_update_from_personality(self, mock_apply):
        """Тест обновления от личности."""
        personality = {
            "extraversion": 0.8,
            "neuroticism": 0.3,
            "openness": 0.6
        }
        
        await self.integration.update_from_personality(personality)
        
        self.assertEqual(self.integration._personality_state["extraversion"], 0.8)
    
    async def test_update_from_decision_support(self):
        """Тест обновления от решения (поддержка)."""
        decision = {"strategy": "PROVIDE_SUPPORT", "emotional_tone": "EMPATHETIC"}
        
        await self.integration.update_from_decision(decision)
        
        # Должна установиться neutral эмоция
        self.assertEqual(self.integration._target_emotions.get("neutral", 0), 0.8)
    
    async def test_update_from_decision_social(self):
        """Тест обновления от решения (социальное)."""
        decision = {"strategy": "ENGAGE_SOCIAL", "emotional_tone": "WARM"}
        
        await self.integration.update_from_decision(decision)
        
        # Должна установиться joy эмоция
        self.assertEqual(self.integration._target_emotions.get("joy", 0), 0.6)


# =============================================================================
# ТЕСТЫ ФАБРИЧНЫХ ФУНКЦИЙ
# =============================================================================

class TestFactoryFunctions(unittest.TestCase):
    """Тесты фабричных функций."""

    def test_create_vtube_client(self):
        """Тест создания клиента."""
        client = create_vtube_client(
            plugin_name="Factory Test",
            plugin_developer="Factory Dev"
        )
        
        self.assertIsInstance(client, VTubeStudioClient)
        self.assertEqual(client.plugin_name, "Factory Test")
        self.assertEqual(client.plugin_developer, "Factory Dev")
    
    def test_create_vtube_integration(self):
        """Тест создания интеграции."""
        integration = create_vtube_integration(auto_connect=False)
        
        self.assertIsInstance(integration, VTubeIntegration)
        self.assertFalse(integration._running)


# =============================================================================
# ИНТЕГРАЦИОННЫЕ ТЕСТЫ (ТРЕБУЮТ VTUBE STUDIO)
# =============================================================================

class TestVTubeStudioIntegration(unittest.TestCase):
    """
    Интеграционные тесты с реальным VTube Studio.
    
    Эти тесты требуют:
    1. Запущенного VTube Studio
    2. Включенного API (порт 8001)
    3. Загруженной модели
    
    Запуск: python -m unittest test_vtube_studio.TestVTubeStudioIntegration -v
    """

    @unittest.skip("Требует запущенного VTube Studio")
    def test_real_connection(self):
        """Тест реального подключения."""
        client = VTubeStudioClient(
            plugin_name="Test Plugin",
            plugin_developer="Test Developer"
        )
        
        async def run_test():
            connected = await client.connect()
            self.assertTrue(connected)
            
            authenticated = await client.authenticate()
            self.assertTrue(authenticated)
            
            await client.disconnect()
        
        asyncio.run(run_test())
    
    @unittest.skip("Требует запущенного VTube Studio")
    def test_real_parameter_set(self):
        """Тест установки реального параметра."""
        client = VTubeStudioClient()
        
        async def run_test():
            await client.connect()
            await client.authenticate()
            
            # Установка параметра
            await client.set_parameter("FaceAngleX", 5.0)
            
            # Проверка
            value = await client.get_parameter_value("FaceAngleX")
            self.assertIsNotNone(value)
            
            await client.disconnect()
        
        asyncio.run(run_test())
    
    @unittest.skip("Требует запущенного VTube Studio")
    def test_real_emotion_set(self):
        """Тест установки реальной эмоции."""
        integration = VTubeIntegration()
        
        async def run_test():
            await integration.connect()
            
            # Установка эмоции
            await integration.set_emotion_by_name("joy", 0.8)
            
            # Ожидание применения
            await asyncio.sleep(1.0)
            
            stats = integration.get_statistics()
            self.assertGreater(stats["current_emotions"].get("joy", 0), 0)
            
            await integration.disconnect()
        
        asyncio.run(run_test())


# =============================================================================
# ЗАПУСК ТЕСТОВ
# =============================================================================

if __name__ == "__main__":
    # Запуск всех тестов
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Добавляем тесты
    suite.addTests(loader.loadTestsFromTestCase(TestDataTypes))
    suite.addTests(loader.loadTestsFromTestCase(TestVTubeStudioClientMocked))
    suite.addTests(loader.loadTestsFromTestCase(TestVTubeIntegrationMocked))
    suite.addTests(loader.loadTestsFromTestCase(TestFactoryFunctions))
    
    # Интеграционные тесты (пропущены по умолчанию)
    # suite.addTests(loader.loadTestsFromTestCase(TestVTubeStudioIntegration))
    
    # Запуск
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Вывод итогов
    print("\n" + "="*60)
    print(f"Всего тестов: {result.testsRun}")
    print(f"Успешно: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Ошибок: {len(result.errors)}")
    print(f"Провалов: {len(result.failures)}")
    print("="*60)

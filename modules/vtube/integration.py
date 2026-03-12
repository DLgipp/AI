"""
VTube Integration - Интеграция VTube Studio с когнитивным пайплайном

Модуль связывает эмоции и состояния личности из когнитивного пайплайна
с анимацией VTuber-модели в VTube Studio.
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

from .controller import VTubeController
from .config import VTubeConfig


logger = logging.getLogger(__name__)


@dataclass
class EmotionState:
    """Состояние эмоции для анимации."""
    emotion: str
    intensity: float  # 0.0 - 1.0
    valence: float    # -1.0 - 1.0
    arousal: float    # 0.0 - 1.0


class VTubeIntegration:
    """
    Интегратор VTube Studio с когнитивным пайплайном.
    
    Автоматически обновляет выражение модели на основе:
    - Эмоций из Perception Layer
    - Состояния личности из Personality Engine
    - Решений из Decision Layer
    
    Работает в фоновом режиме, не блокируя основной процесс.
    
    Пример использования:
        ```python
        # Инициализация
        vtube_integration = VTubeIntegration()
        await vtube_integration.initialize()
        
        # В когнитивном пайплайне после обработки эмоции
        await vtube_integration.update_emotion({
            'dominant_emotion': 'joy',
            'valence': 0.5,
            'arousal': 0.6,
            'joy': 0.7,
            'sadness': 0.1,
            ...
        })
        
        # Обновление состояния личности
        await vtube_integration.update_personality_state({
            'engagement_level': 0.8,
            'emotion_tone': 0.4,
            'emotional_expression': 0.6,
        })
        
        # Отключение
        await vtube_integration.shutdown()
        ```
    """
    
    # Маппинг эмоций из когнитивного пайплайна в VTube
    EMOTION_MAP = {
        'joy': 'joy',
        'sadness': 'sadness',
        'anger': 'anger',
        'fear': 'fear',
        'surprise': 'surprise',
        'disgust': 'neutral',  # Нет специфичной анимации
        'neutral': 'neutral',
    }
    
    def __init__(self, config: Optional[VTubeConfig] = None):
        """
        Инициализация интегратора.
        
        Args:
            config: Конфигурация VTube Studio
        """
        self.config = config or VTubeConfig()
        self._controller = VTubeController(self.config)
        self._initialized = False
        self._running = False
        
        # Текущее состояние
        self._current_emotion: Optional[EmotionState] = None
        self._target_emotion: Optional[EmotionState] = None
        self._personality_state: Dict[str, float] = {}
        
        # Задача фонового обновления
        self._update_task: Optional[asyncio.Task] = None
        
        # Параметры обновления
        self._update_interval = 0.1  # 10 FPS для плавности
        self._emotion_decay_rate = 0.02  # Скорость затухания эмоции
    
    async def initialize(self) -> bool:
        """
        Инициализация подключения к VTube Studio.
        
        Returns:
            True если успешно, False иначе.
        """
        if self._initialized:
            logger.warning("VTube Integration уже инициализирован")
            return True
        
        logger.info("Инициализация VTube Integration...")
        
        # Подключение
        connected = await self._controller.connect()
        
        if connected:
            self._initialized = True
            self._running = True
            
            # Запуск фонового цикла обновления
            self._update_task = asyncio.create_task(self._update_loop())
            
            # Подписка на события
            self._controller.on("connection_lost", self._on_connection_lost)
            self._controller.on("model_loaded", self._on_model_loaded)
            
            logger.info("✓ VTube Integration инициализирован")
            return True
        else:
            logger.error("✗ Не удалось подключиться к VTube Studio")
            return False
    
    async def shutdown(self):
        """Корректное завершение работы."""
        self._running = False
        
        # Остановка фонового цикла
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
        
        # Сброс эмоции в нейтральную
        if self._controller.is_connected:
            await self._controller.set_emotion('neutral')
        
        # Отключение
        await self._controller.disconnect()
        
        self._initialized = False
        logger.info("VTube Integration остановлен")
    
    async def update_emotion(self, emotion_data: Dict[str, Any]):
        """
        Обновление эмоции модели на основе данных из Perception Layer.
        
        Args:
            emotion_data: Данные эмоции из когнитивного пайплайна:
                - dominant_emotion: доминирующая эмоция
                - valence: валентность (-1.0 до 1.0)
                - arousal: возбуждение (0.0 до 1.0)
                - <emotion_name>: интенсивность конкретной эмоции
        """
        if not self._initialized:
            return
        
        # Извлечение данных
        dominant = emotion_data.get('dominant_emotion', 'neutral')
        valence = emotion_data.get('valence', 0.0)
        arousal = emotion_data.get('arousal', 0.0)
        
        # Получение интенсивности доминирующей эмоции
        intensity = emotion_data.get(dominant, 0.5)
        
        # Учёт arousal для усиления
        intensity = min(1.0, intensity * (0.5 + arousal))
        
        # Маппинг эмоции
        vtube_emotion = self.EMOTION_MAP.get(dominant, 'neutral')
        
        # Установка целевой эмоции
        self._target_emotion = EmotionState(
            emotion=vtube_emotion,
            intensity=intensity,
            valence=valence,
            arousal=arousal
        )
        
        logger.debug(f"Эмоция обновлена: {vtube_emotion} (intensity={intensity:.2f})")
    
    async def update_personality_state(self, state: Dict[str, float]):
        """
        Обновление состояния личности для корректировки анимации.
        
        Args:
            state: Состояние личности из Personality Engine:
                - engagement_level: уровень вовлечённости
                - emotion_tone: эмоциональный тон
                - emotional_expression: эмоциональная выразительность
                - extraversion: экстраверсия
                - neuroticism: невротизм
        """
        self._personality_state = state.copy()
        
        # Корректировка на основе личности
        # Например, высокая экстраверсия → более выраженные эмоции
        extraversion = state.get('extraversion', 0.5)
        if extraversion > 0.7:
            self._emotion_intensity_modifier = 1.2
        elif extraversion < 0.3:
            self._emotion_intensity_modifier = 0.8
    
    async def set_expression(self, expression_file: str, active: bool = True):
        """
        Прямая активация выражения лица.
        
        Args:
            expression_file: Путь к файлу выражения
            active: Активировать или деактивировать
        """
        if not self._initialized:
            return
        
        await self._controller.activate_expression(expression_file, active)
    
    async def move_model(
        self,
        x: Optional[float] = None,
        y: Optional[float] = None,
        rotation: Optional[float] = None,
        size: Optional[float] = None,
        duration: float = 0.5
    ):
        """
        Перемещение модели.
        
        Args:
            x: Позиция X
            y: Позиция Y
            rotation: Вращение
            size: Размер
            duration: Длительность
        """
        if not self._initialized:
            return
        
        await self._controller.move_model(x, y, rotation, size, duration)
    
    async def inject_face_parameters(self, parameters: Dict[str, float]):
        """
        Инъекция параметров лица (для lip-sync и т.д.).
        
        Args:
            parameters: Параметры для инъекции
        """
        if not self._initialized:
            return
        
        await self._controller.inject_parameters(parameters)
    
    async def trigger_hotkey(self, hotkey_id: str):
        """
        Активация горячей клавиши модели.
        
        Args:
            hotkey_id: ID горячей клавиши
        """
        if not self._initialized:
            return
        
        await self._controller.trigger_hotkey(hotkey_id)
    
    # ==================== ФОНОВЫЙ ЦИКЛ ====================
    
    async def _update_loop(self):
        """
        Фоновый цикл плавного обновления эмоций.
        
        Работает постоянно, интерполируя текущую эмоцию к целевой.
        """
        while self._running:
            try:
                await self._update_emotion_blend()
                await asyncio.sleep(self._update_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Ошибка в update_loop: {e}")
                await asyncio.sleep(1.0)
    
    async def _update_emotion_blend(self):
        """Плавная интерполяция эмоции к целевой."""
        if not self._controller.is_connected:
            return
        
        # Если нет целевой эмоции, затухаем к neutral
        if self._target_emotion is None:
            if self._current_emotion and self._current_emotion.intensity > 0.01:
                # Затухание
                self._current_emotion.intensity -= self._emotion_decay_rate
                if self._current_emotion.intensity < 0:
                    self._current_emotion = EmotionState('neutral', 0, 0, 0)
                
                await self._controller.set_emotion(
                    self._current_emotion.emotion,
                    self._current_emotion.intensity
                )
            return
        
        # Если текущей эмоции нет, сразу устанавливаем целевую
        if self._current_emotion is None:
            self._current_emotion = self._target_emotion
            await self._controller.set_emotion(
                self._current_emotion.emotion,
                self._current_emotion.intensity
            )
            return
        
        # Плавная интерполяция
        blend_speed = 0.1  # Скорость blending
        
        # Интерполяция интенсивности
        delta = self._target_emotion.intensity - self._current_emotion.intensity
        if abs(delta) > 0.01:
            self._current_emotion.intensity += delta * blend_speed
        
        # Если эмоция изменилась
        if self._target_emotion.emotion != self._current_emotion.emotion:
            # Если новая эмоция сильнее, переключаемся
            if self._target_emotion.intensity > self._current_emotion.intensity + 0.2:
                self._current_emotion.emotion = self._target_emotion.emotion
        
        # Применение
        await self._controller.set_emotion(
            self._current_emotion.emotion,
            self._current_emotion.intensity
        )
        
        # Если целевая эмоция достигнута, сбрасываем
        if (abs(delta) < 0.01 and 
            self._target_emotion.emotion == self._current_emotion.emotion):
            self._target_emotion = None
    
    # ==================== ОБРАБОТЧИКИ СОБЫТИЙ ====================
    
    async def _on_connection_lost(self):
        """Обработчик потери соединения."""
        logger.warning("Соединение с VTube Studio потеряно")
        self._current_emotion = None
        self._target_emotion = None
    
    async def _on_model_loaded(self, model_info):
        """Обработчик загрузки модели."""
        logger.info(f"Модель загружена: {model_info.model_name}")
        # Сброс в нейтральную эмоцию
        await self._controller.set_emotion('neutral')
    
    # ==================== СВОЙСТВА ====================
    
    @property
    def is_initialized(self) -> bool:
        """Проверка инициализации."""
        return self._initialized
    
    @property
    def is_connected(self) -> bool:
        """Проверка подключения."""
        return self._controller.is_connected
    
    @property
    def controller(self) -> VTubeController:
        """Прямой доступ к контроллеру."""
        return self._controller
    
    @property
    def current_emotion(self) -> Optional[EmotionState]:
        """Текущая эмоция модели."""
        return self._current_emotion

"""
Конфигурация модуля VTube Studio
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class VTubeConfig:
    """
    Конфигурация подключения к VTube Studio.
    
    Attributes:
        websocket_url: URL WebSocket сервера VTube Studio
        plugin_name: Название плагина для аутентификации
        plugin_developer: Имя разработчика плагина
        plugin_icon_path: Путь к иконке плагина (опционально)
        auth_token_path: Путь к файлу для хранения токена аутентификации
        reconnect_attempts: Количество попыток переподключения
        reconnect_delay: Задержка между попытками переподключения (сек)
        parameter_update_interval: Интервал обновления параметров (сек)
        enable_face_tracking: Включить отслеживание лица
        enable_expressions: Включить управление выражениями
        enable_items: Включить управление предметами
    """
    
    # Подключение
    websocket_url: str = "ws://localhost:8001"
    
    # Аутентификация
    plugin_name: str = "Akari AI Assistant"
    plugin_developer: str = "Akari Dev Team"
    plugin_icon_path: Optional[str] = None
    auth_token_path: str = "data/vtube_auth_token.json"
    
    # Переподключение
    reconnect_attempts: int = 5
    reconnect_delay: float = 2.0
    
    # Обновления
    parameter_update_interval: float = 0.5  # Минимум 0.5 сек для потери контроля
    enable_face_tracking: bool = True
    enable_expressions: bool = True
    enable_items: bool = True
    
    # Параметры модели по умолчанию
    default_position_x: float = 0.0
    default_position_y: float = 0.0
    default_rotation: float = 0.0
    default_size: float = 0.0
    
    # Эмоции и выражения
    emotion_blend_time: float = 0.3  # Время плавного перехода между эмоциями
    
    @classmethod
    def from_dict(cls, data: dict) -> 'VTubeConfig':
        """Создать конфигурацию из словаря."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
    
    def to_dict(self) -> dict:
        """Преобразовать конфигурацию в словарь."""
        return {
            'websocket_url': self.websocket_url,
            'plugin_name': self.plugin_name,
            'plugin_developer': self.plugin_developer,
            'plugin_icon_path': self.plugin_icon_path,
            'auth_token_path': self.auth_token_path,
            'reconnect_attempts': self.reconnect_attempts,
            'reconnect_delay': self.reconnect_delay,
            'parameter_update_interval': self.parameter_update_interval,
            'enable_face_tracking': self.enable_face_tracking,
            'enable_expressions': self.enable_expressions,
            'enable_items': self.enable_items,
            'default_position_x': self.default_position_x,
            'default_position_y': self.default_position_y,
            'default_rotation': self.default_rotation,
            'default_size': self.default_size,
            'emotion_blend_time': self.emotion_blend_time,
        }

"""
VTube Studio Module - Интеграция с VTube Studio API

Модуль для управления VTuber-моделью в VTube Studio через WebSocket API.
Работает асинхронно, не блокируя основной процесс.

Автор: Акари AI Assistant
"""

from .controller import VTubeController
from .config import VTubeConfig
from .integration import VTubeIntegration, EmotionState
from .types import (
    VTubeAuthStatus,
    VTubeModelInfo,
    VTubeExpression,
    VTubeParameter,
    VTubeHotkey,
    VTubeItem,
    VTubeArtMesh,
    VTubePhysicsOverride,
)

__all__ = [
    'VTubeController',
    'VTubeConfig',
    'VTubeIntegration',
    'EmotionState',
    'VTubeAuthStatus',
    'VTubeModelInfo',
    'VTubeExpression',
    'VTubeParameter',
    'VTubeHotkey',
    'VTubeItem',
    'VTubeArtMesh',
    'VTubePhysicsOverride',
]

__version__ = '1.0.0'

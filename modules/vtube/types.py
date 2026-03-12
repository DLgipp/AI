"""
Типы данных для модуля VTube Studio
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any


class VTubeAuthStatus(Enum):
    """Статус аутентификации."""
    NOT_AUTHENTICATED = "not_authenticated"
    TOKEN_REQUESTED = "token_requested"
    AUTHENTICATED = "authenticated"
    AUTH_FAILED = "auth_failed"
    CONNECTION_LOST = "connection_lost"


@dataclass
class VTubeModelInfo:
    """Информация о текущей модели."""
    model_id: str
    model_name: str
    vts_name: str
    loaded_model_id: str
    time_loaded: float  # Время в секундах
    live2d_item_instance_id: str = ""
    
    @classmethod
    def from_dict(cls, data: dict) -> 'VTubeModelInfo':
        return cls(
            model_id=data.get('modelID', ''),
            model_name=data.get('modelName', ''),
            vts_name=data.get('vtsName', ''),
            loaded_model_id=data.get('loadedModelID', ''),
            time_loaded=data.get('timeLoaded', 0),
            live2d_item_instance_id=data.get('live2DItemInstanceID', '')
        )


@dataclass
class VTubeExpression:
    """Выражение лица (эмоция)."""
    name: str
    file: str
    active: bool = False
    deactivate_when_inactive: bool = False
    fade_in_time: float = 0.0
    fade_out_time: float = 0.0
    
    @classmethod
    def from_dict(cls, data: dict) -> 'VTubeExpression':
        return cls(
            name=data.get('name', ''),
            file=data.get('file', ''),
            active=data.get('active', False),
            deactivate_when_inactive=data.get('deactivateWhenInactive', False),
            fade_in_time=data.get('fadeInTime', 0.0),
            fade_out_time=data.get('fadeOutTime', 0.0)
        )


@dataclass
class VTubeParameter:
    """Параметр отслеживания (лицо, глаза, рот и т.д.)."""
    name: str
    value: float = 0.0
    min_value: float = 0.0
    max_value: float = 0.0
    default_value: float = 0.0
    id: Optional[str] = None
    added_by: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> 'VTubeParameter':
        return cls(
            name=data.get('name', ''),
            value=data.get('value', 0.0),
            min_value=data.get('min', 0.0),
            max_value=data.get('max', 0.0),
            default_value=data.get('defaultValue', 0.0),
            id=data.get('id'),
            added_by=data.get('addedBy')
        )


@dataclass
class VTubeHotkey:
    """Горячая клавиша модели."""
    name: str
    hotkey_id: str
    description: str
    file: str
    hotkey_type: str  # "Expression" или "Animation"
    order: int = 0
    folder: str = ""
    active: bool = True
    auto_deactivate: bool = True
    auto_activate: bool = False
    deactivate_on_key_up: bool = True
    note: str = ""
    
    @classmethod
    def from_dict(cls, data: dict) -> 'VTubeHotkey':
        return cls(
            name=data.get('name', ''),
            hotkey_id=data.get('hotkeyID', ''),
            description=data.get('description', ''),
            file=data.get('file', ''),
            hotkey_type=data.get('hotkeyType', ''),
            order=data.get('order', 0),
            folder=data.get('folder', ''),
            active=data.get('active', True),
            auto_deactivate=data.get('autoDeactivate', True),
            auto_activate=data.get('autoActivate', False),
            deactivate_on_key_up=data.get('deactivateOnKeyUp', True),
            note=data.get('note', '')
        )


@dataclass
class VTubeItem:
    """Предмет (аксессуар) в сцене."""
    instance_id: str
    file_name: str
    order: int
    name: str
    censored: bool = False
    angle: float = 0.0
    current_flip: str = "NONE"
    fps: float = 0.0
    frame_count: int = 0
    position_x: float = 0.0
    position_y: float = 0.0
    size: float = 1.0
    timeline: Optional[Dict[str, Any]] = None
    type_: str = ""
    vts_item_type: str = ""
    visibility: float = 1.0
    
    @classmethod
    def from_dict(cls, data: dict) -> 'VTubeItem':
        return cls(
            instance_id=data.get('instanceID', ''),
            file_name=data.get('fileName', ''),
            order=data.get('order', 0),
            name=data.get('name', ''),
            censored=data.get('censored', False),
            angle=data.get('angle', 0.0),
            current_flip=data.get('currentFlip', 'NONE'),
            fps=data.get('fps', 0.0),
            frame_count=data.get('frameCount', 0),
            position_x=data.get('positionX', 0.0),
            position_y=data.get('positionY', 0.0),
            size=data.get('size', 1.0),
            timeline=data.get('timeline'),
            type_=data.get('type', ''),
            vts_item_type=data.get('vtsItemType', ''),
            visibility=data.get('visibility', 1.0)
        )


@dataclass
class VTubeArtMesh:
    """ArtMesh (часть модели Live2D)."""
    id: str
    name: str
    tags: List[str] = field(default_factory=list)
    color_tint: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> 'VTubeArtMesh':
        return cls(
            id=data.get('Id', ''),
            name=data.get('Name', ''),
            tags=data.get('Tags', []),
            color_tint=data.get('ColorTint')
        )


@dataclass
class VTubePhysicsOverride:
    """Переопределение физики модели."""
    id: str
    value: float
    set_base_value: bool = False
    override_seconds: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'value': self.value,
            'setBaseValue': self.set_base_value,
            'overrideSeconds': self.override_seconds
        }


@dataclass
class VTubeStatistics:
    """Статистика VTube Studio."""
    uptime: float  #秒
    framerate: float
    vts_version: str
    allowed_plugins: int
    models_loaded: int
    window_width: int = 0
    window_height: int = 0
    
    @classmethod
    def from_dict(cls, data: dict) -> 'VTubeStatistics':
        return cls(
            uptime=data.get('uptime', 0),
            framerate=data.get('framerate', 0),
            vts_version=data.get('vtsVersion', ''),
            allowed_plugins=data.get('allowedPlugins', 0),
            models_loaded=data.get('modelsLoaded', 0),
            window_width=data.get('windowWidth', 0),
            window_height=data.get('windowHeight', 0)
        )


# Стандартные параметры VTube Studio
STANDARD_PARAMETERS = {
    # Углы лица
    'FaceAngleX': {'min': -30, 'max': 30, 'default': 0},
    'FaceAngleY': {'min': -30, 'max': 30, 'default': 0},
    'FaceAngleZ': {'min': -30, 'max': 30, 'default': 0},
    
    # Позиция лица
    'FacePositionX': {'min': -1, 'max': 1, 'default': 0},
    'FacePositionY': {'min': -1, 'max': 1, 'default': 0},
    
    # Глаза
    'EyeOpenLeft': {'min': 0, 'max': 1, 'default': 1},
    'EyeOpenRight': {'min': 0, 'max': 1, 'default': 1},
    'EyeLookInLeft': {'min': 0, 'max': 1, 'default': 0},
    'EyeLookInRight': {'min': 0, 'max': 1, 'default': 0},
    'EyeLookOutLeft': {'min': 0, 'max': 1, 'default': 0},
    'EyeLookOutRight': {'min': 0, 'max': 1, 'default': 0},
    'EyeLookUpLeft': {'min': 0, 'max': 1, 'default': 0},
    'EyeLookUpRight': {'min': 0, 'max': 1, 'default': 0},
    'EyeLookDownLeft': {'min': 0, 'max': 1, 'default': 0},
    'EyeLookDownRight': {'min': 0, 'max': 1, 'default': 0},
    
    # Рот
    'MouthOpen': {'min': 0, 'max': 1, 'default': 0},
    'MouthSmileLeft': {'min': 0, 'max': 1, 'default': 0},
    'MouthSmileRight': {'min': 0, 'max': 1, 'default': 0},
    'MouthFrownLeft': {'min': 0, 'max': 1, 'default': 0},
    'MouthFrownRight': {'min': 0, 'max': 1, 'default': 0},
    
    # Щёки
    'CheekPuff': {'min': 0, 'max': 1, 'default': 0},
    'CheekSquintLeft': {'min': 0, 'max': 1, 'default': 0},
    'CheekSquintRight': {'min': 0, 'max': 1, 'default': 0},
    
    # Брови
    'BrowInnerUp': {'min': 0, 'max': 1, 'default': 0},
    'BrowOuterUpLeft': {'min': 0, 'max': 1, 'default': 0},
    'BrowOuterUpRight': {'min': 0, 'max': 1, 'default': 0},
    'BrowDownLeft': {'min': 0, 'max': 1, 'default': 0},
    'BrowDownRight': {'min': 0, 'max': 1, 'default': 0},
}


# Маппинг эмоций на параметры
EMOTION_PARAMETERS_MAP = {
    'joy': {
        'MouthSmileLeft': 1.0,
        'MouthSmileRight': 1.0,
        'EyeOpenLeft': 1.1,  # Чуть шире
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
    'anger': {
        'BrowDownLeft': 0.8,
        'BrowDownRight': 0.8,
        'BrowInnerUp': 0.5,
        'MouthSmileLeft': -0.3,
        'MouthSmileRight': -0.3,
        'EyeOpenLeft': 0.9,
        'EyeOpenRight': 0.9,
    },
    'surprise': {
        'EyeOpenLeft': 1.3,
        'EyeOpenRight': 1.3,
        'BrowOuterUpLeft': 0.7,
        'BrowOuterUpRight': 0.7,
        'MouthOpen': 0.8,
        'FaceAngleY': 5,  # Чуть вверх
    },
    'fear': {
        'EyeOpenLeft': 1.2,
        'EyeOpenRight': 1.2,
        'BrowInnerUp': 0.7,
        'BrowOuterUpLeft': 0.5,
        'BrowOuterUpRight': 0.5,
        'MouthOpen': 0.5,
    },
    'neutral': {
        # Все параметры в default
    }
}

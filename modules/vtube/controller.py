"""
VTube Studio Controller - Основной контроллер для управления VTuber-моделью

Обеспечивает асинхронное подключение к VTube Studio API через WebSocket,
аутентификацию и управление моделью (эмоции, движения, параметры).
"""

import asyncio
import json
import uuid
import base64
import os
from typing import Optional, Dict, Any, List, Callable, Awaitable
from dataclasses import dataclass
import logging

try:
    import websockets
    from websockets.client import WebSocketClientProtocol
except ImportError:
    raise ImportError("Установите websockets: pip install websockets")

from .config import VTubeConfig
from .types import (
    VTubeAuthStatus,
    VTubeModelInfo,
    VTubeExpression,
    VTubeParameter,
    VTubeHotkey,
    VTubeItem,
    VTubeArtMesh,
    VTubeStatistics,
    VTubePhysicsOverride,
    STANDARD_PARAMETERS,
    EMOTION_PARAMETERS_MAP,
)


logger = logging.getLogger(__name__)


@dataclass
class APIError(Exception):
    """Исключение API VTube Studio."""
    error_id: int
    message: str
    
    def __str__(self):
        return f"VTube API Error {self.error_id}: {self.message}"


class VTubeController:
    """
    Контроллер для управления VTuber-моделью в VTube Studio.
    
    Работает в фоновом режиме, не блокируя основной процесс.
    Поддерживает автоматическое переподключение и управление эмоциями.
    
    Пример использования:
        ```python
        controller = VTubeController()
        await controller.connect()
        
        # Установка эмоции
        await controller.set_emotion('joy', intensity=0.8)
        
        # Движение модели
        await controller.move_model(x=0.1, y=-0.2, duration=0.5)
        
        # Инъекция параметров (лицо)
        await controller.inject_parameters({
            'MouthOpen': 0.5,
            'EyeOpenLeft': 0.9,
            'EyeOpenRight': 0.9
        })
        
        await controller.disconnect()
        ```
    """
    
    API_NAME = "VTubeStudioPublicAPI"
    API_VERSION = "1.0"
    
    def __init__(self, config: Optional[VTubeConfig] = None):
        """
        Инициализация контроллера.
        
        Args:
            config: Конфигурация подключения. Если None, используется конфигурация по умолчанию.
        """
        self.config = config or VTubeConfig()
        self._ws: Optional[WebSocketClientProtocol] = None
        self._auth_status = VTubeAuthStatus.NOT_AUTHENTICATED
        self._auth_token: Optional[str] = None
        self._model_info: Optional[VTubeModelInfo] = None
        self._request_handlers: Dict[str, asyncio.Future] = {}
        self._event_handlers: Dict[str, List[Callable]] = {}
        self._running = False
        self._reconnect_attempts = 0
        self._parameter_injection_task: Optional[asyncio.Task] = None
        self._injected_parameters: Dict[str, float] = {}
        self._face_found = False
        
        # Загрузка сохранённого токена
        self._load_auth_token()
    
    # ==================== ПОДКЛЮЧЕНИЕ ====================
    
    async def connect(self) -> bool:
        """
        Подключение к VTube Studio.
        
        Returns:
            True если подключение успешно, False иначе.
        """
        if self._ws and self._ws.open:
            logger.warning("Уже подключено к VTube Studio")
            return True
        
        try:
            logger.info(f"Подключение к {self.config.websocket_url}...")
            self._ws = await websockets.connect(
                self.config.websocket_url,
                ping_interval=20,
                ping_timeout=10,
            )
            
            self._running = True
            self._reconnect_attempts = 0
            
            # Запуск обработчика сообщений
            asyncio.create_task(self._message_handler())
            
            # Аутентификация
            auth_success = await self._authenticate()
            
            if auth_success:
                # Запуск инъекции параметров (если включено)
                if self.config.enable_face_tracking:
                    self._start_parameter_injection()
                
                # Получение информации о модели
                await self._update_model_info()
                
                logger.info("✓ Подключено к VTube Studio")
                self._emit_event("connected")
                return True
            else:
                logger.error("✗ Ошибка аутентификации")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка подключения: {e}")
            self._auth_status = VTubeAuthStatus.CONNECTION_LOST
            return False
    
    async def disconnect(self):
        """Отключение от VTube Studio."""
        self._running = False
        
        # Остановка инъекции параметров
        if self._parameter_injection_task:
            self._parameter_injection_task.cancel()
            try:
                await self._parameter_injection_task
            except asyncio.CancelledError:
                pass
        
        # Очистка инъекций
        if self._ws and self._ws.open:
            await self._clear_injected_parameters()
        
        # Закрытие WebSocket
        if self._ws:
            await self._ws.close()
            self._ws = None
        
        self._auth_status = VTubeAuthStatus.NOT_AUTHENTICATED
        self._emit_event("disconnected")
        logger.info("Отключено от VTube Studio")
    
    async def reconnect(self) -> bool:
        """
        Переподключение к VTube Studio.
        
        Returns:
            True если переподключение успешно, False иначе.
        """
        if self._ws:
            await self.disconnect()
        
        return await self.connect()
    
    # ==================== АУТЕНТИФИКАЦИЯ ====================
    
    def _load_auth_token(self):
        """Загрузка сохранённого токена аутентификации."""
        try:
            if os.path.exists(self.config.auth_token_path):
                with open(self.config.auth_token_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._auth_token = data.get('token')
                    logger.debug("Токен аутентификации загружен")
        except Exception as e:
            logger.warning(f"Не удалось загрузить токен: {e}")
            self._auth_token = None
    
    def _save_auth_token(self):
        """Сохранение токена аутентификации."""
        try:
            os.makedirs(os.path.dirname(self.config.auth_token_path), exist_ok=True)
            with open(self.config.auth_token_path, 'w', encoding='utf-8') as f:
                json.dump({'token': self._auth_token}, f, indent=2)
            logger.debug("Токен аутентификации сохранён")
        except Exception as e:
            logger.warning(f"Не удалось сохранить токен: {e}")
    
    async def _authenticate(self) -> bool:
        """
        Аутентификация в VTube Studio.
        
        Returns:
            True если аутентификация успешна, False иначе.
        """
        try:
            # Если есть сохранённый токен, пробуем сразу аутентифицироваться
            if self._auth_token:
                success = await self._authenticate_with_token()
                if success:
                    return True
            
            # Запрос нового токена
            return await self._request_auth_token()
            
        except Exception as e:
            logger.error(f"Ошибка аутентификации: {e}")
            self._auth_status = VTubeAuthStatus.AUTH_FAILED
            return False
    
    async def _request_auth_token(self) -> bool:
        """Запрос токена аутентификации."""
        self._auth_status = VTubeAuthStatus.TOKEN_REQUESTED
        
        # Подготовка иконки (если есть)
        plugin_icon = ""
        if self.config.plugin_icon_path and os.path.exists(self.config.plugin_icon_path):
            with open(self.config.plugin_icon_path, 'rb') as f:
                plugin_icon = base64.b64encode(f.read()).decode('utf-8')
        
        request = {
            "apiName": self.API_NAME,
            "apiVersion": self.API_VERSION,
            "requestID": str(uuid.uuid4()),
            "messageType": "AuthenticationTokenRequest",
            "data": {
                "pluginName": self.config.plugin_name,
                "pluginDeveloper": self.config.plugin_developer,
            }
        }
        
        if plugin_icon:
            request["data"]["pluginIcon"] = plugin_icon
        
        response = await self._send_request(request)
        
        if response and 'authenticationToken' in response.get('data', {}):
            self._auth_token = response['data']['authenticationToken']
            self._save_auth_token()
            
            # Теперь аутентифицируемся с токеном
            return await self._authenticate_with_token()
        else:
            logger.error("Не удалось получить токен аутентификации")
            self._auth_status = VTubeAuthStatus.AUTH_FAILED
            return False
    
    async def _authenticate_with_token(self) -> bool:
        """Аутентификация с использованием токена."""
        request = {
            "apiName": self.API_NAME,
            "apiVersion": self.API_VERSION,
            "requestID": str(uuid.uuid4()),
            "messageType": "AuthenticationRequest",
            "data": {
                "pluginName": self.config.plugin_name,
                "pluginDeveloper": self.config.plugin_developer,
                "authenticationToken": self._auth_token,
            }
        }
        
        response = await self._send_request(request)
        
        if response and response.get('data', {}).get('authenticated', False):
            self._auth_status = VTubeAuthStatus.AUTHENTICATED
            logger.info("✓ Аутентификация успешна")
            return True
        else:
            # Токен недействителен, удаляем его
            self._auth_token = None
            if os.path.exists(self.config.auth_token_path):
                os.remove(self.config.auth_token_path)
            return False
    
    # ==================== ОБРАБОТКА СООБЩЕНИЙ ====================
    
    async def _message_handler(self):
        """Обработчик входящих сообщений WebSocket."""
        try:
            async for message in self._ws:
                try:
                    data = json.loads(message)
                    await self._process_message(data)
                except json.JSONDecodeError as e:
                    logger.error(f"Ошибка парсинга JSON: {e}")
                except Exception as e:
                    logger.error(f"Ошибка обработки сообщения: {e}")
        except websockets.ConnectionClosed:
            logger.warning("Соединение закрыто")
            self._auth_status = VTubeAuthStatus.CONNECTION_LOST
            self._emit_event("connection_lost")
            
            # Автоматическое переподключение
            if self._running and self._reconnect_attempts < self.config.reconnect_attempts:
                self._reconnect_attempts += 1
                logger.info(f"Переподключение (попытка {self._reconnect_attempts}/{self.config.reconnect_attempts})...")
                await asyncio.sleep(self.config.reconnect_delay)
                await self.reconnect()
        except Exception as e:
            logger.error(f"Ошибка в message_handler: {e}")
    
    async def _process_message(self, data: dict):
        """Обработка входящего сообщения."""
        request_id = data.get('requestID', '')
        message_type = data.get('messageType', '')
        
        # Проверка на ошибку
        if data.get('APIError') is not None or data.get('messageType') == 'APIError':
            error_data = data.get('data', {})
            error_id = error_data.get('errorID', -1)
            error_msg = error_data.get('errorMessage', 'Неизвестная ошибка')
            logger.error(f"API Error {error_id}: {error_msg}")
            
            # Особая обработка ошибки отзыва токена
            if error_id == 50:
                self._auth_token = None
                self._auth_status = VTubeAuthStatus.NOT_AUTHENTICATED
                if os.path.exists(self.config.auth_token_path):
                    os.remove(self.config.auth_token_path)
        else:
            # Отправка ответа в ожидающий Future
            if request_id in self._request_handlers:
                future = self._request_handlers.pop(request_id)
                if not future.done():
                    future.set_result(data)
        
        # Обработка событий
        if message_type:
            self._emit_event(message_type, data)
    
    # ==================== ОТПРАВКА ЗАПРОСОВ ====================
    
    async def _send_request(self, request: dict, timeout: float = 5.0) -> Optional[dict]:
        """
        Отправка запроса и ожидание ответа.
        
        Args:
            request: Данные запроса
            timeout: Таймаут ожидания ответа
        
        Returns:
            Ответ от API или None при ошибке.
        """
        if not self._ws or not self._ws.open:
            logger.error("Нет соединения с VTube Studio")
            return None
        
        request_id = request.get('requestID', str(uuid.uuid4()))
        request['requestID'] = request_id
        
        # Создание Future для ожидания ответа
        future = asyncio.get_event_loop().create_future()
        self._request_handlers[request_id] = future
        
        try:
            # Отправка
            await self._ws.send(json.dumps(request))
            
            # Ожидание ответа
            response = await asyncio.wait_for(future, timeout=timeout)
            return response
            
        except asyncio.TimeoutError:
            logger.error(f"Таймаут запроса {request_id}")
            self._request_handlers.pop(request_id, None)
            return None
        except Exception as e:
            logger.error(f"Ошибка отправки запроса: {e}")
            self._request_handlers.pop(request_id, None)
            return None
    
    # ==================== УПРАВЛЕНИЕ МОДЕЛЬЮ ====================
    
    async def _update_model_info(self):
        """Обновление информации о текущей модели."""
        try:
            request = {
                "apiName": self.API_NAME,
                "apiVersion": self.API_VERSION,
                "requestID": str(uuid.uuid4()),
                "messageType": "CurrentModelRequest",
            }
            
            response = await self._send_request(request)
            
            if response and 'data' in response:
                self._model_info = VTubeModelInfo.from_dict(response['data'])
                logger.info(f"Модель загружена: {self._model_info.model_name}")
                self._emit_event("model_loaded", self._model_info)
        except Exception as e:
            logger.error(f"Ошибка получения информации о модели: {e}")
    
    async def get_model_info(self) -> Optional[VTubeModelInfo]:
        """Получение информации о текущей модели."""
        return self._model_info
    
    async def move_model(
        self,
        x: Optional[float] = None,
        y: Optional[float] = None,
        rotation: Optional[float] = None,
        size: Optional[float] = None,
        duration: float = 0.5,
        relative_to_model: bool = False
    ):
        """
        Перемещение модели.
        
        Args:
            x: Позиция по X (-1000 до 1000), None = без изменений
            y: Позиция по Y (-1000 до 1000), None = без изменений
            rotation: Вращение (-360 до 360), None = без изменений
            size: Размер (-100 до 100), None = без изменений
            duration: Длительность анимации (0-2 сек)
            relative_to_model: Относительные или абсолютные координаты
        """
        request = {
            "apiName": self.API_NAME,
            "apiVersion": self.API_VERSION,
            "requestID": str(uuid.uuid4()),
            "messageType": "MoveModelRequest",
            "data": {
                "timeInSeconds": min(max(duration, 0), 2),
                "valuesAreRelativeToModel": relative_to_model,
            }
        }
        
        # Добавляем только указанные параметры
        data = request["data"]
        if x is not None:
            data["positionX"] = min(max(x, -1000), 1000)
        if y is not None:
            data["positionY"] = min(max(y, -1000), 1000)
        if rotation is not None:
            data["rotation"] = min(max(rotation, -360), 360)
        if size is not None:
            data["size"] = min(max(size, -100), 100)
        
        response = await self._send_request(request)
        
        if response and response.get('data', {}).get('moved', False):
            logger.debug(f"Модель перемещена: x={x}, y={y}, rot={rotation}, size={size}")
    
    async def reset_model_position(self):
        """Сброс позиции модели в значение по умолчанию."""
        await self.move_model(
            x=self.config.default_position_x,
            y=self.config.default_position_y,
            rotation=self.config.default_rotation,
            size=self.config.default_size,
            duration=self.config.emotion_blend_time
        )
    
    # ==================== ЭМОЦИИ И ВЫРАЖЕНИЯ ====================
    
    async def set_emotion(self, emotion: str, intensity: float = 1.0, blend_time: Optional[float] = None):
        """
        Установка эмоции через инъекцию параметров.
        
        Args:
            emotion: Название эмоции ('joy', 'sadness', 'anger', 'surprise', 'fear', 'neutral')
            intensity: Интенсивность (0.0 до 1.0)
            blend_time: Время плавного перехода (сек)
        """
        if emotion not in EMOTION_PARAMETERS_MAP:
            logger.warning(f"Неизвестная эмоция: {emotion}")
            return
        
        blend_time = blend_time or self.config.emotion_blend_time
        
        # Получаем параметры эмоции
        emotion_params = EMOTION_PARAMETERS_MAP[emotion].copy()
        
        # Применяем интенсивность
        for param, value in emotion_params.items():
            emotion_params[param] = value * intensity
        
        # Для neutral сбрасываем все параметры
        if emotion == 'neutral':
            await self._inject_emotion_params(emotion_params, blend_time)
        else:
            # Смешиваем с neutral для плавности
            await self._inject_emotion_params(emotion_params, blend_time)
        
        logger.debug(f"Эмоция установлена: {emotion} (интенсивность: {intensity})")
    
    async def _inject_emotion_params(self, params: Dict[str, float], blend_time: float):
        """Инъекция параметров эмоции."""
        # Добавляем FaceFound для активации
        injected_params = {
            'faceFound': True,
            'mode': 'set',
            'parameterValues': []
        }
        
        for param_id, value in params.items():
            # Ограничиваем значение в допустимых пределах
            if param_id in STANDARD_PARAMETERS:
                param_info = STANDARD_PARAMETERS[param_id]
                value = min(max(value, param_info['min']), param_info['max'])
            
            injected_params['parameterValues'].append({
                'id': param_id,
                'value': value,
            })
        
        request = {
            "apiName": self.API_NAME,
            "apiVersion": self.API_VERSION,
            "requestID": str(uuid.uuid4()),
            "messageType": "InjectParameterDataRequest",
            "data": injected_params
        }
        
        await self._send_request(request)
    
    async def activate_expression(
        self,
        expression_file: str,
        active: bool = True,
        fade_time: float = 0.5
    ):
        """
        Активация/деактивация выражения лица.
        
        Args:
            expression_file: Путь к файлу выражения (.exp3.json)
            active: Активно или нет
            fade_time: Время плавного перехода (0-2 сек)
        """
        request = {
            "apiName": self.API_NAME,
            "apiVersion": self.API_VERSION,
            "requestID": str(uuid.uuid4()),
            "messageType": "ExpressionActivationRequest",
            "data": {
                "expressionFile": expression_file,
                "fadeTime": min(max(fade_time, 0), 2),
                "active": active,
            }
        }
        
        response = await self._send_request(request)
        
        if response:
            status = "активировано" if active else "деактивировано"
            logger.debug(f"Выражение {expression_file} {status}")
    
    async def get_expressions(self, details: bool = True) -> List[VTubeExpression]:
        """
        Получение списка выражений.
        
        Args:
            details: Включать детальную информацию
        
        Returns:
            Список выражений
        """
        request = {
            "apiName": self.API_NAME,
            "apiVersion": self.API_VERSION,
            "requestID": str(uuid.uuid4()),
            "messageType": "ExpressionStateRequest",
            "data": {
                "details": details,
            }
        }
        
        response = await self._send_request(request)
        
        if response and 'data' in response and 'expressions' in response['data']:
            return [
                VTubeExpression.from_dict(expr)
                for expr in response['data']['expressions']
            ]
        return []
    
    # ==================== ИНЪЕКЦИЯ ПАРАМЕТРОВ ====================
    
    def _start_parameter_injection(self):
        """Запуск фонового обновления инъекций параметров."""
        self._parameter_injection_task = asyncio.create_task(
            self._parameter_injection_loop()
        )
    
    async def _parameter_injection_loop(self):
        """Фоновый цикл инъекции параметров."""
        while self._running and self._ws and self._ws.open:
            if self._injected_parameters:
                await self._send_injected_parameters()
            
            # Обновляем чаще чем interval, чтобы не потерять контроль
            await asyncio.sleep(self.config.parameter_update_interval / 2)
    
    async def inject_parameters(self, parameters: Dict[str, float], face_found: bool = True):
        """
        Инъекция параметров (для отслеживания лица).
        
        Важно: Нужно отправлять минимум раз в секунду, иначе контроль теряется.
        
        Args:
            parameters: Словарь {параметр: значение}
            face_found: Обнаружено ли лицо
        """
        self._injected_parameters = parameters.copy()
        self._face_found = face_found
        
        # Отправляем немедленно
        if self._running and self._ws and self._ws.open:
            await self._send_injected_parameters()
    
    async def _send_injected_parameters(self):
        """Отправка текущих инъекций параметров."""
        if not self._injected_parameters:
            return
        
        request = {
            "apiName": self.API_NAME,
            "apiVersion": self.API_VERSION,
            "requestID": str(uuid.uuid4()),
            "messageType": "InjectParameterDataRequest",
            "data": {
                "faceFound": self._face_found,
                "mode": "set",
                "parameterValues": [
                    {'id': param_id, 'value': value}
                    for param_id, value in self._injected_parameters.items()
                ]
            }
        }
        
        await self._send_request(request, timeout=1.0)
    
    async def _clear_injected_parameters(self):
        """Очистка инъекций параметров."""
        self._injected_parameters = {}
        self._face_found = False
        
        # Отправляем пустую инъекцию
        request = {
            "apiName": self.API_NAME,
            "apiVersion": self.API_VERSION,
            "requestID": str(uuid.uuid4()),
            "messageType": "InjectParameterDataRequest",
            "data": {
                "faceFound": False,
                "mode": "set",
                "parameterValues": []
            }
        }
        
        await self._send_request(request)
    
    # ==================== ГОРЯЧИЕ КЛАВИШИ ====================
    
    async def get_hotkeys(self, model_id: Optional[str] = None) -> List[VTubeHotkey]:
        """
        Получение списка горячих клавиш.
        
        Args:
            model_id: ID модели (None = текущая)
        
        Returns:
            Список горячих клавиш
        """
        request = {
            "apiName": self.API_NAME,
            "apiVersion": self.API_VERSION,
            "requestID": str(uuid.uuid4()),
            "messageType": "HotkeysInCurrentModelRequest",
        }
        
        if model_id:
            request["data"] = {"modelID": model_id}
        
        response = await self._send_request(request)
        
        if response and 'data' in response and 'availableHotkeys' in response['data']:
            return [
                VTubeHotkey.from_dict(hk)
                for hk in response['data']['availableHotkeys']
            ]
        return []
    
    async def trigger_hotkey(self, hotkey_id: str):
        """
        Активация горячей клавиши.
        
        Args:
            hotkey_id: ID горячей клавиши
        """
        request = {
            "apiName": self.API_NAME,
            "apiVersion": self.API_VERSION,
            "requestID": str(uuid.uuid4()),
            "messageType": "HotkeyTriggerRequest",
            "data": {
                "hotkeyID": hotkey_id,
            }
        }
        
        response = await self._send_request(request)
        
        if response:
            logger.debug(f"Горячая клавиша активирована: {hotkey_id}")
    
    # ==================== ПРЕДМЕТЫ ====================
    
    async def load_item(
        self,
        file_name: str,
        position_x: float = 0,
        position_y: float = 0,
        size: float = 1,
        rotation: float = 0,
        fade_time: float = 0.5,
        order: int = 1,
        unload_on_disconnect: bool = True
    ) -> Optional[str]:
        """
        Загрузка предмета (аксессуара).
        
        Args:
            file_name: Имя файла предмета
            position_x: Позиция X
            position_y: Позиция Y
            size: Размер
            rotation: Вращение
            fade_time: Время появления
            order: Порядок отображения
            unload_on_disconnect: Удалять при отключении
        
        Returns:
            instance_id предмета или None при ошибке
        """
        request = {
            "apiName": self.API_NAME,
            "apiVersion": self.API_VERSION,
            "requestID": str(uuid.uuid4()),
            "messageType": "ItemLoadRequest",
            "data": {
                "fileName": file_name,
                "positionX": position_x,
                "positionY": position_y,
                "size": size,
                "rotation": rotation,
                "fadeTime": fade_time,
                "order": order,
                "unloadWhenPluginDisconnects": unload_on_disconnect,
            }
        }
        
        response = await self._send_request(request)
        
        if response and 'data' in response:
            instance_id = response['data'].get('instanceID')
            logger.debug(f"Предмет загружен: {file_name} (ID: {instance_id})")
            return instance_id
        return None
    
    async def unload_item(self, instance_id: str):
        """Выгрузка предмета."""
        request = {
            "apiName": self.API_NAME,
            "apiVersion": self.API_VERSION,
            "requestID": str(uuid.uuid4()),
            "messageType": "ItemUnloadRequest",
            "data": {
                "instanceID": instance_id,
            }
        }
        
        await self._send_request(request)
        logger.debug(f"Предмет выгружен: {instance_id}")
    
    async def get_items(self) -> List[VTubeItem]:
        """Получение списка предметов."""
        request = {
            "apiName": self.API_NAME,
            "apiVersion": self.API_VERSION,
            "requestID": str(uuid.uuid4()),
            "messageType": "ItemListRequest",
        }
        
        response = await self._send_request(request)
        
        if response and 'data' in response and 'items' in response['data']:
            return [
                VTubeItem.from_dict(item)
                for item in response['data']['items']
            ]
        return []
    
    # ==================== ART MESH ====================
    
    async def get_art_meshes(self) -> List[VTubeArtMesh]:
        """Получение списка ArtMesh."""
        request = {
            "apiName": self.API_NAME,
            "apiVersion": self.API_VERSION,
            "requestID": str(uuid.uuid4()),
            "messageType": "ArtMeshListRequest",
        }
        
        response = await self._send_request(request)
        
        if response and 'data' in response and 'artMeshes' in response['data']:
            return [
                VTubeArtMesh.from_dict(mesh)
                for mesh in response['data']['artMeshes']
            ]
        return []
    
    async def tint_art_mesh(
        self,
        mesh_id: str,
        r: int = 255,
        g: int = 255,
        b: int = 255,
        a: int = 255,
        mix_with_lighting: float = 1.0
    ):
        """
        Тонирование ArtMesh.
        
        Args:
            mesh_id: ID ArtMesh
            r: Красный (0-255)
            g: Зелёный (0-255)
            b: Синий (0-255)
            a: Прозрачность (0-255)
            mix_with_lighting: Смешивание с освещением сцены (0-1)
        """
        request = {
            "apiName": self.API_NAME,
            "apiVersion": self.API_VERSION,
            "requestID": str(uuid.uuid4()),
            "messageType": "ColorTintRequest",
            "data": {
                "colorTint": {
                    "colorR": r,
                    "colorG": g,
                    "colorB": b,
                    "colorA": a,
                    "mixWithSceneLightingColor": mix_with_lighting,
                },
                "artMeshMatcher": {
                    "tintAll": False,
                    "idExact": [mesh_id],
                }
            }
        }
        
        await self._send_request(request)
    
    # ==================== ФИЗИКА ====================
    
    async def override_physics(
        self,
        overrides: List[VTubePhysicsOverride],
    ):
        """
        Переопределение физики модели.
        
        Args:
            overrides: Список переопределений физики
        """
        request = {
            "apiName": self.API_NAME,
            "apiVersion": self.API_VERSION,
            "requestID": str(uuid.uuid4()),
            "messageType": "SetCurrentModelPhysicsRequest",
            "data": {
                "strengthOverrides": [ov.to_dict() for ov in overrides],
            }
        }
        
        await self._send_request(request)
    
    # ==================== СТАТИСТИКА ====================
    
    async def get_statistics(self) -> Optional[VTubeStatistics]:
        """Получение статистики VTube Studio."""
        request = {
            "apiName": self.API_NAME,
            "apiVersion": self.API_VERSION,
            "requestID": str(uuid.uuid4()),
            "messageType": "StatisticsRequest",
        }
        
        response = await self._send_request(request)
        
        if response and 'data' in response:
            return VTubeStatistics.from_dict(response['data'])
        return None
    
    async def is_face_found(self) -> bool:
        """Проверка, обнаружено ли лицо."""
        request = {
            "apiName": self.API_NAME,
            "apiVersion": self.API_VERSION,
            "requestID": str(uuid.uuid4()),
            "messageType": "FaceFoundRequest",
        }
        
        response = await self._send_request(request)
        
        if response and 'data' in response:
            return response['data'].get('faceFound', False)
        return False
    
    # ==================== СОБЫТИЯ ====================
    
    def on(self, event: str, handler: Callable):
        """
        Подписка на событие.
        
        Args:
            event: Название события
            handler: Обработчик (функция или корутина)
        
        Доступные события:
            - connected: Подключение
            - disconnected: Отключение
            - connection_lost: Потеря соединения
            - model_loaded: Загрузка модели
            - model_unloaded: Выгрузка модели
        """
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(handler)
    
    def _emit_event(self, event: str, *args, **kwargs):
        """Испуск события."""
        if event in self._event_handlers:
            for handler in self._event_handlers[event]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        asyncio.create_task(handler(*args, **kwargs))
                    else:
                        handler(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Ошибка в обработчике события {event}: {e}")
    
    # ==================== СВОЙСТВА ====================
    
    @property
    def is_connected(self) -> bool:
        """Проверка подключения."""
        return self._ws is not None and self._ws.open
    
    @property
    def is_authenticated(self) -> bool:
        """Проверка аутентификации."""
        return self._auth_status == VTubeAuthStatus.AUTHENTICATED
    
    @property
    def auth_status(self) -> VTubeAuthStatus:
        """Текущий статус аутентификации."""
        return self._auth_status
    
    @property
    def model_info(self) -> Optional[VTubeModelInfo]:
        """Информация о текущей модели."""
        return self._model_info

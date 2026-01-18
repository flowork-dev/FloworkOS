########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\gateway_connector_service\__init__.py total lines 187 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from flowork_kernel.services.gateway_connector_service.handlers.base_handler import BaseHandler, CURRENT_PAYLOAD_VERSION

import importlib
import os
import logging
import asyncio
import socketio
import multiprocessing
import requests
import time
import json
from typing import Dict, Any
from dotenv import load_dotenv

from flowork_kernel.services.base_service import BaseService
from flowork_kernel.singleton import Singleton
from flowork_kernel.router import StrategyRouter
from flowork_kernel.fac_enforcer import FacRuntime

from .handlers.system_handler import SystemHandler
from .handlers.workflow_handler import WorkflowHandler
from .handlers.data_handler import DataHandler
from .handlers.component_handler import ComponentHandler
from .handlers.ai_handler import AIHandler

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env'))

CURRENT_PAYLOAD_VERSION = 2

class SocketIOLogHandler(logging.Handler):
    """
    Custom Log Handler that intercepts logs from Core and emits them
    to the Gateway via SocketIO ('engine_log' event).
    """
    def __init__(self, service):
        super().__init__()
        self.service = service
        self.setFormatter(logging.Formatter('%(message)s'))

    def emit(self, record):
        if record.name.startswith(('socketio', 'engineio', 'aiohttp', 'urllib3', 'requests', 'werkzeug')):
            return

        if not self.service.is_authenticated or not self.service.sio.connected:
            return

        try:
            msg = self.format(record)

            log_target_user = getattr(record, 'user_id', None)
            if not log_target_user:
                 log_target_user = self.service.user_id

            payload = {
                'timestamp': record.created,
                'level': record.levelname,
                'message': msg,
                'source': 'core',
                'engine_id': self.service.engine_id,
                'user_id': log_target_user,
                'metadata': {
                    'logger': record.name,
                    'func': record.funcName,
                    'lineno': record.lineno
                }
            }

            if self.service._main_loop and self.service._main_loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    self.service.emit_to_gateway('engine_log', payload),
                    self.service._main_loop
                )
        except Exception:
            self.handleError(record)

class GatewayConnectorService(BaseService):
    def __init__(self, kernel, service_id):
        self.cells = {}
        if not hasattr(self, 'logger'):
            self.logger = logging.getLogger('LazyHub')

        super().__init__(kernel, service_id)

        self.sio = socketio.AsyncClient(
            logger=False,
            engineio_logger=False,
            reconnection=True,
            reconnection_delay=5,
            reconnection_attempts=0
        )
        self.gateway_url = os.getenv("FLOWORK_GATEWAY_URL") or os.getenv("GATEWAY_API_URL", "http://gateway:8000")
        self.engine_token = os.getenv("FLOWORK_ENGINE_TOKEN")
        self.engine_id = os.getenv("FLOWORK_ENGINE_ID")
        self.kernel_services = {}
        self.user_id = None
        self.internal_api_url = "http://flowork_core:8989"
        self._hb_task = None
        self._watchdog_task = None
        self._main_loop = None
        self.router = StrategyRouter(["default","fast","thorough"])
        self._pending_swarm_tasks: Dict[str, asyncio.Future] = {}
        self._pending_swarm_tasks_lock = asyncio.Lock()
        self.g_active_sessions: Dict[str, FacRuntime] = {}

        self.retry_count = 0

        self.logger.info(f"GatewayConnectorService initialized. URL: {self.gateway_url}")

        self.handlers = [
            SystemHandler(self),
            WorkflowHandler(self),
            DataHandler(self),
            ComponentHandler(self),
            AIHandler(self)
        ]
        self.register_event_handlers()
        self.is_authenticated = False
        self.is_running = True

    def execute_sync(self, cell_name, *args, **kwargs):
        module = self._load_cell(cell_name)
        return module.run(self, *args, **kwargs)

    async def execute_async(self, cell_name, *args, **kwargs):
        module = self._load_cell(cell_name)
        return await module.run(self, *args, **kwargs)

    def _load_cell(self, cell_name):
        if cell_name not in self.cells:
            try:
                module = importlib.import_module(f".{cell_name}", package=__package__)
                self.cells[cell_name] = module
                if hasattr(self, 'logger'):
                    self.logger.info(f"[LazyHub] ✅ Loaded: {cell_name}.py")
            except Exception as e:
                if hasattr(self, 'logger'):
                    self.logger.error(f"[LazyHub] ❌ Failed to load '{cell_name}': {e}")
                raise e
        return self.cells[cell_name]

    async def _send_engine_ready(self, *args, **kwargs):
        return await self.execute_async('_send_engine_ready', *args, **kwargs)

    async def _run_watchdog(self, *args, **kwargs):
        return await self.execute_async('_run_watchdog', *args, **kwargs)

    async def send_gateway_swarm_task(self, *args, **kwargs):
        return await self.execute_async('send_gateway_swarm_task', *args, **kwargs)

    def _resolve_home_gateway(self, *args, **kwargs):
        return self.execute_sync('_resolve_home_gateway', *args, **kwargs)

    def set_kernel_services(self, *args, **kwargs):
        return self.execute_sync('set_kernel_services', *args, **kwargs)

    async def emit_to_gateway(self, *args, **kwargs):
        return await self.execute_async('emit_to_gateway', *args, **kwargs)

    def forward_event_to_gateway(self, *args, **kwargs):
        return self.execute_sync('forward_event_to_gateway', *args, **kwargs)

    async def _async_forward_payload(self, *args, **kwargs):
        return await self.execute_async('_async_forward_payload', *args, **kwargs)

    def register_event_handlers(self, *args, **kwargs):
        return self.execute_sync('register_event_handlers', *args, **kwargs)

    async def _engine_heartbeat(self, *args, **kwargs):
        return await self.execute_async('_engine_heartbeat', *args, **kwargs)

    async def start(self, *args, **kwargs):
        return await self.execute_async('start', *args, **kwargs)

    async def stop(self, *args, **kwargs):
        return await self.execute_async('stop', *args, **kwargs)

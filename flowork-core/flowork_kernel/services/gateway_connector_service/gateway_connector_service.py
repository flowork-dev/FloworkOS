########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\gateway_connector_service\gateway_connector_service.py total lines 432 
########################################################################

import socketio
import os
import asyncio
import logging
import uuid
import json
import multiprocessing
import requests
import time
import sqlite3
import threading
import traceback
from dotenv import load_dotenv
from typing import Dict, Any

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
                'user_id': log_target_user, # Inject ID disini
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
        self._main_loop = None # [MATA-MATA] Capture the main asyncio loop
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
        self.is_running = True # Flag untuk loop abadi

    async def _send_engine_ready(self):
        retry = 0
        while '/engine-socket' not in self.sio.namespaces and retry < 15:
            await asyncio.sleep(1); retry += 1

        if '/engine-socket' not in self.sio.namespaces: return

        payload = {
            "engine_id": self.engine_id,
            "token": self.engine_token,
            "internal_api_url": self.internal_api_url,
            "version": "7.2-skeleton-stable",
            "capabilities": ["workflow", "modules", "tools", "apps"]
        }
        try:
            await self.sio.emit('engine_ready', payload, namespace='/engine-socket')
        except Exception as e:
            self.logger.warning(f"Failed to send engine_ready: {e}")

    async def _run_watchdog(self):
        """
        [PROTECTED TASK] Runs watchdog ping.
        Inherits Tier 1-2 protection via handle_injury wrapper.
        """
        try:
            while self.is_running:
                try:
                    if self.sio.connected and '/engine-socket' in self.sio.namespaces:
                        await self.sio.emit('core:ping', {'ts': int(time.time())}, namespace='/engine-socket')

                    await asyncio.sleep(3)

                except Exception as e:
                    self.logger.error(f"Watchdog hiccup: {e}")
                    await asyncio.sleep(5)

        except asyncio.CancelledError:
            pass

    async def send_gateway_swarm_task(self, target_engine_id: str, task_payload: Dict[str, Any]) -> Dict[str, Any]:
        task_id = task_payload.get("task_id")
        if not task_id: return {"error": "task_id missing"}
        if not self.sio.connected: return {"error": "Socket disconnected"}

        loop = asyncio.get_running_loop()
        task_future = loop.create_future()

        async with self._pending_swarm_tasks_lock:
            self._pending_swarm_tasks[task_id] = task_future

        try:
            await self.emit_to_gateway('core:request_swarm_task', {"target_engine_id": target_engine_id, "task_payload": task_payload})
            return await asyncio.wait_for(task_future, timeout=task_payload.get("swarm_timeout_s", 30.0))
        except Exception as e:
            return {"error": str(e)}
        finally:
            async with self._pending_swarm_tasks_lock:
                self._pending_swarm_tasks.pop(task_id, None)

    def _resolve_home_gateway(self) -> str:
        try:
            base_url = self.gateway_url.replace('/api/v1', '').rstrip('/')
            res = requests.get(f"{base_url}/api/v1/cluster/resolve-home?key={self.engine_id}", timeout=3.0)
            if res.status_code == 200:
                home_url = res.json().get("url")
                if home_url: return home_url
            return self.gateway_url
        except:
            return self.gateway_url

    def set_kernel_services(self, kernel_services: dict):
        """
        [MATA-MATA] Late Binding for EventBus.
        """
        self.kernel_services = kernel_services
        eb = self.kernel_services.get("event_bus")
        if eb:
            if hasattr(eb, "set_main_loop") and self._main_loop:
                eb.set_main_loop(self._main_loop)

            self.logger.info("[MATA-MATA] Injecting Gateway Forwarder into EventBus...")
            eb.subscribe("*", "gateway_gui_forwarder", self.forward_event_to_gateway)
        else:
            try:
                eb = Singleton.get_instance("event_bus")
                if eb:
                    if hasattr(eb, "set_main_loop") and self._main_loop:
                        eb.set_main_loop(self._main_loop)

                    self.logger.info("[MATA-MATA] Injecting Gateway Forwarder via Singleton...")
                    eb.subscribe("*", "gateway_gui_forwarder", self.forward_event_to_gateway)
            except:
                self.logger.error("[MATA-MATA] Failed to bind EventBus!")

    async def emit_to_gateway(self, event_name: str, payload: dict):
        try:
            if not self.sio.connected or '/engine-socket' not in self.sio.namespaces:
                return
            await self.sio.emit(event_name, payload, namespace='/engine-socket')
        except Exception as e:
            self.logger.error(f"Emit error: {e}")

    def forward_event_to_gateway(self, event_name, subscriber_id, payload):
        """
        [FIXED BRIDGE V4] Synchronous entry point for EventBus.
        """
        GUI_SAFE = [
            "SHOW_DEBUG_POPUP",
            "WORKFLOW_EXECUTION_UPDATE",
            "NODE_METRIC_UPDATE",
            "WORKFLOW_LOG_ENTRY",
            "NODE_STATUS_UPDATE",
            "EXECUTION_PROGRESS",
            "APP_LOG_STREAM",
            "APP_PROGRESS",
            "APP_RESULT",
            "APP_JOB_FINISHED",
            "EXECUTION_LOG"
        ]

        if event_name not in GUI_SAFE:
            return

        if not self._main_loop:
            try:
                self._main_loop = asyncio.get_event_loop()
                if not self._main_loop.is_running():
                     return
            except:
                return

        try:
            if isinstance(payload, dict) and 'user_id' in payload:
                payload['_target_user_id'] = payload['user_id']

            asyncio.run_coroutine_threadsafe(
                self._async_forward_payload(event_name, payload),
                self._main_loop
            )
        except Exception as e:
            self.logger.error(f"[MATA-MATA] Bridge Dispatch Error {event_name}: {e}")

    async def _async_forward_payload(self, event_name, payload):
        """Actual async sender that runs in the loop"""
        if not self.sio.connected:
            return

        target_user_id = self.user_id
        if isinstance(payload, dict):

            extracted_uid = payload.get('_target_user_id') or payload.get('user_id')

            if extracted_uid and str(extracted_uid).lower() == "system":
                extracted_uid = self.user_id

            if extracted_uid:
                target_user_id = extracted_uid

        v_payload = {
            'v': CURRENT_PAYLOAD_VERSION,
            'payload': {
                'event_name': event_name,
                'event_data': payload,
                'user_id': str(target_user_id) if target_user_id else None
            }
        }
        await self.sio.emit('forward_event_to_gui', v_payload, namespace='/engine-socket')

    def register_event_handlers(self):
        for handler in self.handlers:
            handler.register_events()

    async def _engine_heartbeat(self):
        """
        [PROTECTED TASK] Vital signs monitoring.
        Inherits Tier 1-2 protection.
        """
        while self.is_running:
            try:
                if not self.sio.connected or '/engine-socket' not in self.sio.namespaces:
                    await asyncio.sleep(5); continue

                cpu = psutil.cpu_percent() if PSUTIL_AVAILABLE else 0
                mem = psutil.virtual_memory().percent if PSUTIL_AVAILABLE else 0

                payload = {
                    'engine_id': self.engine_id,
                    'user_id': self.user_id,
                    'ts': int(time.time()),
                    'cpu_percent': cpu,
                    'memory_percent': mem,
                    'metrics': {'pid': os.getpid(), 'active_fac_sessions': len(self.g_active_sessions)}
                }
                await self.sio.emit('engine_vitals_update', payload, namespace='/engine-socket')

            except Exception as e:
                self.logger.warning(f"Heartbeat skipped: {e}")

            await asyncio.sleep(15)

    async def start(self):
        """
        [OVERRIDDEN] Async Entry Point.
        Mengimplementasikan IMMORTALITY MATRIX untuk koneksi SocketIO.
        """
        try:
            self._main_loop = asyncio.get_running_loop()
            self.logger.info(f"[MATA-MATA] Main Async Loop Captured: {self._main_loop}")
        except:
            self.logger.error("[MATA-MATA] FAILED TO CAPTURE MAIN LOOP IN START!")

        try:
            job_evt = multiprocessing.Event()
            Singleton.set_instance(multiprocessing.Event, job_evt)
            Singleton.set_instance("job_event", job_evt)
            self.logger.info("✅ [MATA-MATA] Job Event (Bell) registered to Singleton.")
        except Exception as e:
            self.logger.error(f"❌ [MATA-MATA] Failed to register Job Event: {e}")

        try:
            eb = self.kernel_services.get("event_bus") or Singleton.get_instance("event_bus")
            if eb and hasattr(eb, "set_main_loop"):
                eb.set_main_loop(self._main_loop)
                self.logger.info("✅ [MATA-MATA] EventBus Main Loop Activated! IPC Bridge is OPEN.")
            else:
                self.logger.warning("⚠️ [MATA-MATA] EventBus not found or incompatible during start.")
        except Exception as e:
            self.logger.error(f"❌ [MATA-MATA] Failed to activate EventBus loop: {e}")

        try:
            root_logger = logging.getLogger()
            if not any(isinstance(h, SocketIOLogHandler) for h in root_logger.handlers):
                log_courier = SocketIOLogHandler(self)
                root_logger.addHandler(log_courier)
                self.logger.info("✅ [MATA-MATA] Log Courier attached. Core logs will be streamed to GUI.")
        except Exception as e:
            self.logger.error(f"❌ [MATA-MATA] Failed to attach Log Courier: {e}")

        if not self.engine_id or not self.engine_token or not self.gateway_url:
            self.logger.critical("MISSING ENV VARS for Gateway Connection!")
            return

        resolved_url = self._resolve_home_gateway()
        if "gw-" in resolved_url and "gateway" not in resolved_url:
            resolved_url = "http://gateway:8000"

        connect_url = resolved_url.replace("http", "ws")
        if "gateway" in connect_url and ":" not in connect_url.split("//")[1]:
            connect_url = connect_url.rstrip("/") + ":8000"

        auth_payload = {'engine_id': self.engine_id, 'token': self.engine_token}

        @self.sio.on('connect', namespace='/engine-socket')
        async def on_connect():
            self.logger.info(f"✅ [MATA-MATA] SOCKET PHYSICALLY CONNECTED")
            await self.sio.emit('authenticate', auth_payload, namespace='/engine-socket')
            self.set_kernel_services(self.kernel_services)
            self.retry_count = 0 # Reset luka kalau berhasil konek

        @self.sio.on('auth_success', namespace='/engine-socket')
        async def on_auth_success(data):
            self.user_id = data.get('user_id'); self.is_authenticated = True
            self.logger.info(f"🛡️ [MATA-MATA] AUTH SUCCESS. User: {self.user_id}")
            asyncio.create_task(self._send_engine_ready())

            if not self._hb_task:
                self._hb_task = asyncio.create_task(self._engine_heartbeat())
            if not self._watchdog_task:
                self._watchdog_task = asyncio.create_task(self._run_watchdog())

        @self.sio.on('disconnect', namespace='/engine-socket')
        async def on_disconnect():
            self.is_authenticated = False
            self.logger.warning("🔌 Socket Disconnected.")

        self.logger.info(f"📡 [MATA-MATA] Client connecting to: {connect_url}")

        while self.is_running:
            try:
                await self.sio.connect(
                    connect_url,
                    auth=auth_payload,
                    namespaces=['/engine-socket'],
                    socketio_path="/api/socket.io",
                    transports=['websocket']
                )
                await self.sio.wait()

            except Exception as e:

                self.logger.error(f"Gateway Connection Error: {e}")

                self.retry_count += 1
                if self.retry_count > 5:
                    self.logger.critical("⚠️ Too many connection failures. Escalating...")
                    await asyncio.sleep(10)
                else:
                    await asyncio.sleep(5)

                self.is_authenticated = False

    async def stop(self):
        self.is_running = False
        if self.sio: await self.sio.disconnect()

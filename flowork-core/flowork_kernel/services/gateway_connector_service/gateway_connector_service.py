########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\gateway_connector_service\gateway_connector_service.py total lines 334 
########################################################################

"""
document : https://flowork.cloud/p-analisis-mendalam-gatewayconnectorservice-jantung-komunikasi-kernel-fl-id.html
"""

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
from dotenv import load_dotenv
from typing import Dict, Any
from flowork_kernel.services.base_service import BaseService
from flowork_kernel.singleton import Singleton
from flowork_kernel.services.database_service.database_service import DatabaseService
from flowork_kernel.services.variable_manager_service.variable_manager_service import VariableManagerService
from flowork_kernel.router import StrategyRouter
from flowork_kernel.fac_enforcer import FacRuntime
from flowork_kernel.exceptions import PermissionDeniedError

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
        self.gateway_url = os.getenv("GATEWAY_API_URL", "http://gateway:8000")
        self.engine_token = os.getenv("FLOWORK_ENGINE_TOKEN")
        self.engine_id = os.getenv("FLOWORK_ENGINE_ID")
        self.kernel_services = {}
        self.user_id = None
        self.internal_api_url = None
        self._hb_task = None

        self._watchdog_task = None

        self.router = StrategyRouter(["default","fast","thorough"])

        self._pending_swarm_tasks: Dict[str, asyncio.Future] = {}
        self._pending_swarm_tasks_lock = asyncio.Lock()

        self.g_active_sessions: Dict[str, FacRuntime] = {}

        self.logger.info(f"GatewayConnectorService (Socket.IO Client Mode) initialized. URL: {self.gateway_url}")

        self.handlers = [
            SystemHandler(self),
            WorkflowHandler(self),
            DataHandler(self),
            ComponentHandler(self),
            AIHandler(self)
        ]
        self.register_event_handlers()

    async def _run_watchdog(self):
        """
        (English Hardcode) Active Connection Stabilizer (Watchdog).
        Strategies:
        1. Micro-Ping every 3 seconds to keep Cloudflare tunnel alive.
        2. Force keep-alive on the socket engine.
        """
        self.logger.info("[Watchdog] Active Connection Stabilizer STARTED (Interval: 3s).")
        try:
            while True:
                if self.sio.connected:
                    try:
                        await self.sio.emit('core:ping', {'ts': int(time.time())}, namespace='/engine-socket')
                    except Exception as e:
                        self.logger.warning(f"[Watchdog] Ping failed (Connection unstable?): {e}")
                else:
                    self.logger.debug("[Watchdog] Socket disconnected. Waiting for auto-reconnect...")

                await asyncio.sleep(3)

        except asyncio.CancelledError:
            self.logger.info("[Watchdog] Task Cancelled (Service Stopping or Disconnected).")
        except Exception as e:
            self.logger.error(f"[Watchdog] CRITICAL FAILURE: {e}", exc_info=True)

    async def send_gateway_swarm_task(self, target_engine_id: str, task_payload: Dict[str, Any]) -> Dict[str, Any]:
        task_id = task_payload.get("task_id")
        if not task_id:
            return {"error": "send_gateway_swarm_task: task_payload must have a 'task_id'."}

        if not self.sio.connected:
            self.logger.error(f"[Gateway R6] Cannot send task {task_id}: Socket not connected.")
            return {"error": "GatewayError: Core is not connected to Gateway."}

        loop = asyncio.get_running_loop()
        task_future = loop.create_future()

        async with self._pending_swarm_tasks_lock:
            self._pending_swarm_tasks[task_id] = task_future

        self.logger.info(f"[Gateway R6] Sending swarm task {task_id} to Gateway (Target: {target_engine_id})...")

        try:
            await self.emit_to_gateway('core:request_swarm_task', {
                "target_engine_id": target_engine_id,
                "task_payload": task_payload
            })

            timeout_s = task_payload.get("swarm_timeout_s", 30.0)

            result = await asyncio.wait_for(task_future, timeout=timeout_s)
            self.logger.info(f"[Gateway R6] Received result for task {task_id}.")
            return result

        except asyncio.TimeoutError:
            self.logger.error(f"[Gateway R6] Task {task_id} timed out waiting for Gateway result.")
            return {"error": f"GatewayTimeout: Task {task_id} timed out after {timeout_s}s."}
        except Exception as e:
            self.logger.error(f"[Gateway R6] Failed to send/wait for task {task_id}: {e}", exc_info=True)
            return {"error": f"GatewayError: Failed to send task: {e}"}
        finally:
            async with self._pending_swarm_tasks_lock:
                self._pending_swarm_tasks.pop(task_id, None)

    def _resolve_home_gateway(self) -> str:
        try:
            resolver_url = f"{self.gateway_url}/api/v1/cluster/resolve-home?key={self.engine_id}"
            self.logger.info(f"[GatewayConnector] Resolving home gateway via: {resolver_url}")
            res = requests.get(resolver_url, timeout=5.0)
            res.raise_for_status()
            data = res.json()
            home_url = data.get("home_url")
            if not home_url:
                raise ValueError("Resolver did not return 'home_url'")
            self.logger.info(f"[GatewayConnector] Home gateway resolved to: {data.get('home_id')}")
            return home_url
        except Exception as e:
            self.logger.error(f"[GatewayConnector] CRITICAL: Failed to resolve home gateway: {e}")
            self.logger.warning("[GatewayConnector] Fallback: connecting to default GATEWAY_API_URL.")
            return self.gateway_url

    def set_kernel_services(self, kernel_services: dict):
        self.kernel_services = kernel_services
        self.logger.info(f"Kernel services injected. {len(self.kernel_services)} services loaded.")

        event_bus = self.kernel_services.get("event_bus")
        if event_bus:
            self.logger.info("[GatewayConnector] Subscribing to main event bus for GUI forwarding.")
            event_bus.subscribe("*", "gateway_gui_forwarder", self.forward_event_to_gateway)
        else:
            self.logger.error("[GatewayConnector] EventBus not found in kernel_services. GUI forwarding will fail.")

    async def emit_to_gateway(self, event_name: str, payload: dict):

        try:
            if not self.sio.connected:
                self.logger.warning(f"[Core Emitter] Cannot send '{event_name}': Socket not connected.")
                return

            if event_name != 'core:agent_token' and not event_name.startswith('core:request_swarm_task') and event_name != 'core:ping':
                self.logger.info(f"[Core Emitter] Sending '{event_name}' to Gateway. Session: {payload.get('session_id')}")

            await self.sio.emit(event_name, payload, namespace='/engine-socket')

        except Exception as e:
            self.logger.error(f"[Core Emitter] Failed to emit '{event_name}': {e}", exc_info=True)

    async def forward_event_to_gateway(self, event_name, subscriber_id, payload):
        try:

            if not self.sio.connected:
                return

            GUI_SAFE_EVENTS = [
                "SHOW_DEBUG_POPUP",
                "WORKFLOW_EXECUTION_UPDATE",
                "NODE_METRIC_UPDATE",
                "WORKFLOW_LOG_ENTRY",
                "JOB_COMPLETED_CHECK" # Added for debug visibility
            ]

            if event_name in GUI_SAFE_EVENTS:

                target_user_id = self.user_id
                if isinstance(payload, dict) and '_target_user_id' in payload:
                    target_user_id = payload.get('_target_user_id')

                versioned_payload = {
                    'v': CURRENT_PAYLOAD_VERSION,
                    'payload': {
                        'event_name': event_name,
                        'event_data': payload,
                        'user_id': target_user_id
                    }
                }
                await self.sio.emit('forward_event_to_gui', versioned_payload, namespace='/engine-socket')

        except Exception as e:
            self.logger.error(f"[GatewayConnector] Error forwarding event '{event_name}': {e}", exc_info=True)

    def _get_safe_roots(self):
        roots = [os.path.abspath(self.kernel.project_root_path)]

        user_home = os.path.expanduser('~')
        common_dirs = ['Desktop', 'Documents', 'Downloads', 'Pictures', 'Music', 'Videos']
        for d in common_dirs:
            path = os.path.join(user_home, d)
            if os.path.isdir(path):
                roots.append(os.path.abspath(path))

        if PSUTIL_AVAILABLE:
            try:
                for partition in psutil.disk_partitions():
                    roots.append(os.path.abspath(partition.mountpoint))
            except Exception:
                pass
        else:
            if os.name == "nt":
                import string
                for letter in string.ascii_uppercase:
                    drive = f"{letter}:\\"
                    if os.path.isdir(drive):
                        roots.append(drive)

        return sorted(list(set(roots)))

    def register_event_handlers(self):
        for handler in self.handlers:
            handler.register_events()
            self.logger.info(f"Registered events from handler: {handler.__class__.__name__}")

    async def _engine_heartbeat(self):
        self.logger.info("[GatewayConnector] Heartbeat task started.")
        try:
            while True:
                try:
                    cpu_usage = psutil.cpu_percent(interval=None)
                    mem = psutil.virtual_memory()

                    payload = {
                        'engine_id': self.engine_id,
                        'user_id': self.user_id,
                        'internal_api_url': self.internal_api_url,
                        'ts': int(time.time()),
                        'cpu_percent': cpu_usage,
                        'memory_percent': mem.percent,
                        'metrics': {
                            'pid': os.getpid(),
                            'active_fac_sessions': len(self.g_active_sessions),
                            'cpuPercent': cpu_usage,       # (English Hardcode) Added for redundancy
                            'memoryPercent': mem.percent  # (English Hardcode) Added for redundancy
                        }
                    }

                    await self.sio.emit('engine_vitals_update', payload, namespace='/engine-socket')
                except Exception as e:
                    self.logger.error(f"[GatewayConnector] Heartbeat error: {e}", exc_info=True)
                await asyncio.sleep(10)
        except asyncio.CancelledError:
            self.logger.info("[GatewayConnector] Heartbeat task cancelled.")
        except Exception as e:
            self.logger.error(f"[GatewayConnector] Heartbeat task crashed: {e}", exc_info=True)

    async def start(self):
        if not self.engine_id or not self.engine_token or not self.gateway_url:
            self.logger.error("GatewayConnectorService not properly set up. Missing URL, Engine ID or Token.")
            return
        self.logger.info(f"Starting GatewayConnectorService, resolving home gateway from {self.gateway_url}...")
        resolved_http_url = self._resolve_home_gateway()

        if resolved_http_url.startswith("https://"):
            connect_url = resolved_http_url.replace("https://", "wss://")
        else:
            connect_url = resolved_http_url.replace("http://", "ws://")

        socketio_path = "/api/socket.io"
        self.logger.info(f"[GatewayConnector] Connecting to WebSocket at: {connect_url} with path {socketio_path}")

        auth_payload = {
            'engine_id': self.engine_id,
            'token': self.engine_token
        }

        while True:
            try:
                await self.sio.connect(
                    connect_url,
                    headers={"Authorization": f"Bearer {self.engine_token}"},
                    auth=auth_payload,
                    namespaces=['/engine-socket'],
                    socketio_path=socketio_path
                )
                self.logger.info(f"[GatewayConnector] Initial connection successful to {connect_url}")
                await self.sio.wait()
            except socketio.exceptions.ConnectionError as e:
                self.logger.error(f"Failed to connect to Gateway at {connect_url}: {e}. Retrying in 5 seconds...")
            except Exception as e:
                self.logger.error(f"An unexpected error occurred in GatewayConnectorService: {e}", exc_info=True)
            finally:
                self.logger.info("GatewayConnectorService stopped. Will attempt to restart connection loop.")
                await asyncio.sleep(5)

    async def stop(self):
        self.logger.info("Stopping GatewayConnectorService...")
        try:
            if self._hb_task and not self._hb_task.done():
                self._hb_task.cancel()
            if self.sio.connected:
                await self.sio.disconnect()
        except Exception as e:
            self.logger.error(f"Error during disconnect: {e}", exc_info=True)

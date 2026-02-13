########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\gateway_connector_service\send_gateway_swarm_task.py total lines 53 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from flowork_kernel.services.gateway_connector_service.handlers.base_handler import BaseHandler, CURRENT_PAYLOAD_VERSION

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

CURRENT_PAYLOAD_VERSION = 2


async def run(hub, target_engine_id: str, task_payload: Dict[str, Any]) -> Dict[str, Any]:
    task_id = task_payload.get('task_id')
    if not task_id:
        return {'error': 'task_id missing'}
    if not hub.sio.connected:
        return {'error': 'Socket disconnected'}
    loop = asyncio.get_running_loop()
    task_future = loop.create_future()
    async with hub._pending_swarm_tasks_lock:
        hub._pending_swarm_tasks[task_id] = task_future
    try:
        await (await hub.execute_async('emit_to_gateway', 'core:request_swarm_task', {'target_engine_id': target_engine_id, 'task_payload': task_payload}))
        return await asyncio.wait_for(task_future, timeout=task_payload.get('swarm_timeout_s', 30.0))
    except Exception as e:
        return {'error': str(e)}
    finally:
        async with hub._pending_swarm_tasks_lock:
            hub._pending_swarm_tasks.pop(task_id, None)

########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\gateway_connector_service\_run_watchdog.py total lines 51 
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


async def run(hub):
    """
        [PROTECTED TASK] Runs watchdog ping.
        Inherits Tier 1-2 protection via handle_injury wrapper.
        """
    try:
        while hub.is_running:
            try:
                if hub.sio.connected and '/engine-socket' in hub.sio.namespaces:
                    await hub.sio.emit('core:ping', {'ts': int(time.time())}, namespace='/engine-socket')
                await asyncio.sleep(3)
            except Exception as e:
                hub.logger.error(f'Watchdog hiccup: {e}')
                await asyncio.sleep(5)
    except asyncio.CancelledError:
        pass

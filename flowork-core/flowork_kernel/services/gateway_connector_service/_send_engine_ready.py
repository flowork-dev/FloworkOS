########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\gateway_connector_service\_send_engine_ready.py total lines 47 
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
    retry = 0
    while '/engine-socket' not in hub.sio.namespaces and retry < 15:
        await asyncio.sleep(1)
        retry += 1
    if '/engine-socket' not in hub.sio.namespaces:
        return
    payload = {'engine_id': hub.engine_id, 'token': hub.engine_token, 'internal_api_url': hub.internal_api_url, 'version': '7.2-skeleton-stable', 'capabilities': ['workflow', 'modules', 'tools', 'apps']}
    try:
        await hub.sio.emit('engine_ready', payload, namespace='/engine-socket')
    except Exception as e:
        hub.logger.warning(f'Failed to send engine_ready: {e}')

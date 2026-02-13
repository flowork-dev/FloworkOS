########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\gateway_connector_service\forward_event_to_gateway.py total lines 55 
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


def run(hub, event_name, subscriber_id, payload):
    """
        [FIXED BRIDGE V4] Synchronous entry point for EventBus (Core -> Gateway).
        """
    GUI_SAFE = ['SHOW_DEBUG_POPUP', 'WORKFLOW_EXECUTION_UPDATE', 'NODE_METRIC_UPDATE', 'WORKFLOW_LOG_ENTRY', 'NODE_STATUS_UPDATE', 'EXECUTION_PROGRESS', 'APP_LOG_STREAM', 'APP_PROGRESS', 'APP_RESULT', 'APP_JOB_FINISHED', 'EXECUTION_LOG']
    if event_name not in GUI_SAFE:
        return
    if not hub._main_loop:
        try:
            hub._main_loop = asyncio.get_event_loop()
            if not hub._main_loop.is_running():
                return
        except:
            return
    try:
        if isinstance(payload, dict) and 'user_id' in payload:
            payload['_target_user_id'] = payload['user_id']
        asyncio.run_coroutine_threadsafe(hub.execute_sync('_async_forward_payload', event_name, payload), hub._main_loop)
    except Exception as e:
        hub.logger.error(f'[MATA-MATA] Bridge Dispatch Error {event_name}: {e}')

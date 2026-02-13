########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\gateway_connector_service\_async_forward_payload.py total lines 48 
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


async def run(hub, event_name, payload):
    """Actual async sender that runs in the loop"""
    if not hub.sio.connected:
        return
    target_user_id = hub.user_id
    if isinstance(payload, dict):
        extracted_uid = payload.get('_target_user_id') or payload.get('user_id')
        if extracted_uid and str(extracted_uid).lower() == 'system':
            extracted_uid = hub.user_id
        if extracted_uid:
            target_user_id = extracted_uid
    v_payload = {'v': CURRENT_PAYLOAD_VERSION, 'payload': {'event_name': event_name, 'event_data': payload, 'user_id': str(target_user_id) if target_user_id else None}}
    await hub.sio.emit('forward_event_to_gui', v_payload, namespace='/engine-socket')

########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\gateway_connector_service\set_kernel_services.py total lines 56 
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


def run(hub, kernel_services: dict):
    """
        [MATA-MATA] Late Binding for EventBus.
        """
    hub.kernel_services = kernel_services
    eb = hub.kernel_services.get('event_bus')
    if eb:
        if hasattr(eb, 'set_main_loop') and hub._main_loop:
            eb.set_main_loop(hub._main_loop)
        hub.logger.info('[MATA-MATA] Injecting Gateway Forwarder into EventBus...')
        eb.subscribe('*', 'gateway_gui_forwarder', hub.forward_event_to_gateway)
    else:
        try:
            eb = Singleton.get_instance('event_bus')
            if eb:
                if hasattr(eb, 'set_main_loop') and hub._main_loop:
                    eb.set_main_loop(hub._main_loop)
                hub.logger.info('[MATA-MATA] Injecting Gateway Forwarder via Singleton...')
                eb.subscribe('*', 'gateway_gui_forwarder', hub.forward_event_to_gateway)
        except:
            hub.logger.error('[MATA-MATA] Failed to bind EventBus!')

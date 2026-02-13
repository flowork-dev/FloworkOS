########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\workflow_executor_service\start_listeners.py total lines 49 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import logging
import uuid
import time
import json
import sqlite3
import multiprocessing
import asyncio
import random
import threading
from datetime import datetime
from typing import Dict, Any, List, Optional
from flowork_kernel.services.base_service import BaseService
from flowork_kernel.singleton import Singleton
from flowork_kernel.services.database_service.database_service import DatabaseService
from flowork_kernel.outcome import OutcomeMeter
from flowork_kernel.analyst import Analyst, AnalystReport


def run(hub):
    try:
        if not hub.db_service:
            hub.db_service = Singleton.get_instance(DatabaseService)
        hub.event_bus = Singleton.get_instance('event_bus')
        hub.app_manager = Singleton.get_instance('app_service')
        try:
            if hub.kernel and hasattr(hub.kernel, 'services'):
                hub.gateway_connector = hub.kernel.services.get('gateway_connector_service')
        except:
            pass
        if not hub.db_service:
            hub.logger.error('CRITICAL: Missing DB Service from Singleton in start_listeners.')
            return
        if not hub.event_bus:
            hub.logger.error('CRITICAL: Missing Event Bus from Singleton in start_listeners.')
            return
        hub.event_bus.subscribe('JOB_COMPLETED_CHECK', 'workflow_executor_service.check', hub._on_job_completed)
        hub._watchdog_thread = threading.Thread(target=hub._watchdog_loop, daemon=True)
        hub._watchdog_thread.start()
        hub.logger.info('Service initialized. Watchdog Thread started.')
    except Exception as e:
        hub.logger.error(f'CRITICAL: Failed to initialize service instances: {e}', exc_info=True)
        hub.db_service = None
        hub.event_bus = None

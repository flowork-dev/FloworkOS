########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\workflow_executor_service\_publish_node_status.py total lines 36 
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


def run(hub, execution_id: str, node_id: str, status: str):
    if hub.event_bus:
        try:
            target_user = hub.execution_user_cache.get(execution_id)
            payload = {'job_id': execution_id, 'execution_id': execution_id, 'node_id': node_id, 'status': status, 'timestamp': time.time(), '_target_user_id': target_user}
            hub.event_bus.publish('node_status_update', payload, publisher_id='SYSTEM')
            if not hub.gateway_connector and hub.kernel and hasattr(hub.kernel, 'services'):
                hub.gateway_connector = hub.kernel.services.get('gateway_connector_service')
            if hub.gateway_connector:
                hub.gateway_connector.forward_event_to_gateway('NODE_STATUS_UPDATE', 'vip_express', payload)
        except Exception as e:
            hub.logger.error(f'Failed to publish node_status_update: {e}')

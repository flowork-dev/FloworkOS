########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\workflow_executor_service\_publish_workflow_status.py total lines 40 
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


def run(hub, execution_id: str, status: str, end_time: Optional[float]=None, outcome: Optional[Dict[str, Any]]=None, analysis: Optional[Dict[str, Any]]=None):
    try:
        target_user = hub.execution_user_cache.get(execution_id)
        status_data = {'status': status}
        if end_time:
            status_data['end_time'] = end_time
        event_payload = {'job_id': execution_id, 'status_data': status_data, 'outcome': outcome or {}, 'analysis': analysis or {}, '_target_user_id': target_user}
        if hub.event_bus:
            hub.event_bus.publish('WORKFLOW_EXECUTION_UPDATE', event_payload, publisher_id='SYSTEM')
        if not hub.gateway_connector and hub.kernel and hasattr(hub.kernel, 'services'):
            hub.gateway_connector = hub.kernel.services.get('gateway_connector_service')
        if hub.gateway_connector:
            hub.gateway_connector.forward_event_to_gateway('WORKFLOW_EXECUTION_UPDATE', 'vip_express', event_payload)
        hub.logger.info(f'Published WORKFLOW_EXECUTION_UPDATE: {status} for {execution_id}')
    except Exception as e:
        hub.logger.error(f'Failed to publish WORKFLOW_EXECUTION_UPDATE for {execution_id}: {e}', exc_info=True)

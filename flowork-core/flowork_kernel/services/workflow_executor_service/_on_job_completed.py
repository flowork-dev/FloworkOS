########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\workflow_executor_service\_on_job_completed.py total lines 42 
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


async def run(hub, event_name: str, subscriber_id: str, event_data: Dict[str, Any]):
    execution_id = event_data.get('execution_id')
    job_id = event_data.get('job_id')
    status = event_data.get('status')
    if not execution_id:
        return
    hub.logger.info(f'Job {job_id} ({status}) finished. Checking next steps...')
    node_id = await hub.execute_async('_get_node_id_by_job', job_id)
    if node_id:
        node_status = 'SUCCESS' if status == 'DONE' else 'FAILED'
        await hub.execute_async('_publish_node_status', execution_id, node_id, node_status)
        msg = f'Node finished with status: {node_status}'
        lvl = 'SUCCESS' if status == 'DONE' else 'ERROR'
        await hub.execute_async('_publish_log', execution_id, node_id, msg, lvl)
        if status == 'DONE' or status == 'FAILED':
            await (await hub.execute_async('_queue_downstream_nodes', execution_id, node_id, job_id, status))
    async with hub._completion_lock:
        await (await hub.execute_async('_check_workflow_completion', execution_id))

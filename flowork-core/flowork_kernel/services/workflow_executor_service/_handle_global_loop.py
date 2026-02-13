########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\workflow_executor_service\_handle_global_loop.py total lines 78 
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


async def run(hub, execution_id: str, conn) -> bool:
    loop_data = hub.execution_loop_cache.get(execution_id)
    if not loop_data:
        return False
    config = loop_data.get('config', {})
    current_iter = loop_data.get('current', 1)
    max_iter = int(config.get('iterations', 1))
    if current_iter >= max_iter:
        hub.logger.info(f'[Loop] Execution {execution_id} reached max iterations ({max_iter}). Stopping.')
        return False
    is_delay_enabled = config.get('isDelayEnabled', False)
    if is_delay_enabled:
        delay_type = config.get('delayType', 'static')
        delay_seconds = 0.0
        if delay_type == 'static':
            delay_seconds = float(config.get('delayStatic', 1))
        elif delay_type == 'random_range':
            mn = float(config.get('delayRandomMin', 1))
            mx = float(config.get('delayRandomMax', 5))
            if mn > mx:
                (mn, mx) = (mx, mn)
            delay_seconds = random.uniform(mn, mx)
        if delay_seconds > 0:
            hub.logger.info(f'[Loop] Sleeping for {delay_seconds:.2f}s before iteration {current_iter + 1}...')
            await asyncio.sleep(delay_seconds)
    next_iter = current_iter + 1
    loop_data['current'] = next_iter
    workflow_id = loop_data.get('workflow_id')
    user_id = hub.execution_user_cache.get(execution_id)
    hub.logger.info(f'[Loop] Restarting workflow {execution_id} (Iteration {next_iter}/{max_iter})...')
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT node_id FROM Nodes WHERE workflow_id = ? AND node_type = 'flowork.core.trigger.start'", (workflow_id,))
        start_node = cursor.fetchone()
        if not start_node:
            cursor.execute('\n                    SELECT T1.node_id FROM Nodes AS T1\n                    LEFT JOIN Edges AS T2 ON T1.node_id = T2.target_node_id\n                    WHERE T1.workflow_id = ? AND T2.edge_id IS NULL\n                    LIMIT 1\n                    ', (workflow_id,))
            start_node = cursor.fetchone()
        if not start_node:
            hub.logger.error(f'[Loop] Failed to find start node for restart.')
            return False
        start_node_id = start_node[0]
        new_job_id = str(uuid.uuid4())
        cursor.execute("\n                INSERT INTO Jobs (job_id, execution_id, node_id, status, input_data, workflow_id, user_id)\n                VALUES (?, ?, ?, 'PENDING', '{}', ?, ?)\n                ", (new_job_id, execution_id, start_node_id, workflow_id, user_id))
        conn.commit()
        await hub.execute_async('_publish_node_status', execution_id, start_node_id, 'RUNNING')
        job_event = Singleton.get_instance(multiprocessing.Event)
        if job_event:
            job_event.set()
        await hub.execute_async('_publish_workflow_status', execution_id, 'RUNNING', end_time=None)
        return True
    except Exception as e:
        hub.logger.error(f'[Loop] Failed to restart workflow: {e}')
        conn.rollback()
        return False

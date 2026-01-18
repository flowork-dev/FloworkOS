########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\workflow_executor_service\start_workflow_execution.py total lines 72 
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


def run(hub, workflow_id: str, user_id: str, initial_payload: dict, strategy: str='default') -> (str, str):
    if not hub.db_service:
        hub.logger.error('DB service not available. Cannot start workflow.')
        raise Exception('DatabaseService not initialized.')
    conn = None
    try:
        execution_id = str(uuid.uuid4())
        start_job_id = str(uuid.uuid4())
        hub.execution_user_cache[execution_id] = user_id
        if initial_payload and isinstance(initial_payload, dict):
            loop_cfg = initial_payload.get('_runtime_loop_config')
            if loop_cfg:
                hub.execute_sync('set_execution_loop_config', execution_id, loop_cfg, workflow_id)
        conn = hub.db_service.create_connection()
        if not conn:
            raise Exception('Failed to create DB connection.')
        cursor = conn.cursor()
        cursor.execute('BEGIN IMMEDIATE;')
        cursor.execute("SELECT node_id FROM Nodes WHERE workflow_id = ? AND node_type = 'flowork.core.trigger.start'", (workflow_id,))
        start_node = cursor.fetchone()
        if not start_node:
            cursor.execute('\n                    SELECT T1.node_id FROM Nodes AS T1\n                    LEFT JOIN Edges AS T2 ON T1.node_id = T2.target_node_id\n                    WHERE T1.workflow_id = ? AND T2.edge_id IS NULL\n                    LIMIT 1\n                    ', (workflow_id,))
            start_node = cursor.fetchone()
        if not start_node:
            raise Exception(f'Cannot find a start node (no inputs) for workflow_id {workflow_id}')
        start_node_id = start_node[0]
        try:
            cursor.execute("\n                    INSERT INTO Executions (execution_id, workflow_id, user_id, strategy, status, created_at, gas_budget_hint)\n                    VALUES (?, ?, ?, ?, 'RUNNING', CURRENT_TIMESTAMP, ?)\n                    ", (execution_id, workflow_id, user_id, strategy, 10000))
        except sqlite3.Error as e:
            hub.logger.warning(f"(R5) Failed to create 'Executions' record, maybe table doesn't exist? {e}")
            pass
        safe_input_json = json.dumps(initial_payload, default=str)
        cursor.execute("\n                INSERT INTO Jobs (job_id, execution_id, node_id, status, input_data, workflow_id, user_id)\n                VALUES (?, ?, ?, 'PENDING', ?, ?, ?)\n                ", (start_job_id, execution_id, start_node_id, safe_input_json, workflow_id, user_id))
        conn.commit()
        hub.execute_sync('_publish_node_status', execution_id, start_node_id, 'RUNNING')
        hub.execute_sync('_publish_log', execution_id, start_node_id, 'Workflow started', 'SUCCESS')
        job_event = Singleton.get_instance(multiprocessing.Event)
        if job_event:
            job_event.set()
        return (execution_id, start_job_id)
    except Exception as e:
        if conn:
            conn.rollback()
        hub.logger.error(f'Failed to start workflow execution for {workflow_id}: {e}', exc_info=True)
        raise
    finally:
        if conn:
            conn.close()

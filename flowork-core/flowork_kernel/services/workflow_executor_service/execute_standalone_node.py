########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\workflow_executor_service\execute_standalone_node.py total lines 90 
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


async def run(hub, payload: dict):
    """
        [FIXED BY FLOWORK DEV]
        Executes a single node as an entry point with STANDALONE PROTECTION.
        Avoids DB IntegrityError when workflow_id is missing.
        """
    hub.logger.info(f'Executing standalone node request: {payload}')
    raw_node_id = payload.get('node_id')
    user_id = payload.get('user_id', 'direct_command')
    forced_execution_id = payload.get('execution_id')
    forced_job_id = payload.get('job_id')
    input_data = payload.get('input')
    if input_data is None:
        input_data = {k: v for (k, v) in payload.items() if k not in ['node_id', 'user_id', 'engine_id', 'job_id', 'execution_id']}
    if not raw_node_id:
        hub.logger.error("execute_standalone_node failed: 'node_id' is missing.")
        return
    if hub.app_manager and raw_node_id in hub.app_manager.registry.get('apps', {}).get('data', {}):
        hub.logger.info(f"[SDK Bridge] Found App Node '{raw_node_id}'. Delegating (Standalone Mode).")
        ctx = {'user_context': {'user_id': user_id}, 'job_id': forced_job_id or str(uuid.uuid4()), 'workflow_id': None}
        pass
    if not hub.db_service:
        hub.logger.error('execute_standalone_node failed: DB Service unavailable.')
        return
    conn = None
    try:
        conn = hub.db_service.create_connection()
        cursor = conn.cursor()
        resolved_node_id = raw_node_id
        workflow_id = None
        try:
            uuid.UUID(raw_node_id)
            cursor.execute('SELECT workflow_id FROM Nodes WHERE node_id = ?', (raw_node_id,))
            row = cursor.fetchone()
            if row:
                workflow_id = row[0]
        except ValueError:
            cursor.execute('SELECT node_id, workflow_id FROM Nodes WHERE node_type = ? ORDER BY rowid DESC LIMIT 1', (raw_node_id,))
            row = cursor.fetchone()
            if row:
                resolved_node_id = row[0]
                workflow_id = row[1]
        if not workflow_id:
            workflow_id = '00000000-0000-0000-0000-000000000000'
        execution_id = forced_execution_id if forced_execution_id else str(uuid.uuid4())
        job_id = forced_job_id if forced_job_id else str(uuid.uuid4())
        hub.execution_user_cache[execution_id] = user_id
        cursor.execute("\n                INSERT OR IGNORE INTO Executions (execution_id, workflow_id, user_id, strategy, status, created_at, gas_budget_hint)\n                VALUES (?, ?, ?, ?, 'RUNNING', CURRENT_TIMESTAMP, ?)\n                ", (execution_id, workflow_id, user_id, 'manual_node_trigger', 10000))
        safe_input_json = json.dumps(input_data, default=str)
        cursor.execute("\n                INSERT INTO Jobs (job_id, execution_id, node_id, status, input_data, workflow_id, user_id)\n                VALUES (?, ?, ?, 'PENDING', ?, ?, ?)\n                ", (job_id, execution_id, resolved_node_id, safe_input_json, workflow_id, user_id))
        conn.commit()
        hub.logger.info(f'[Standalone] DB Execution started! Exec ID: {execution_id}')
        await hub.execute_async('_publish_node_status', execution_id, resolved_node_id, 'RUNNING')
        await hub.execute_async('_publish_log', execution_id, resolved_node_id, f'Standalone Job Started: {job_id}', 'INFO')
        job_event = Singleton.get_instance(multiprocessing.Event)
        if job_event:
            job_event.set()
        return {'status': 'queued', 'job_id': job_id, 'execution_id': execution_id}
    except Exception as e:
        hub.logger.error(f'execute_standalone_node Exception: {e}', exc_info=True)
        if conn:
            conn.rollback()
        return {'error': str(e)}
    finally:
        if conn:
            conn.close()

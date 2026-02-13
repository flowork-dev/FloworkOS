########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\workflow_executor_service\_queue_downstream_nodes_sync.py total lines 72 
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


def run(hub, conn, execution_id, finished_node_id, finished_job_id, status='DONE'):
    try:
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT target_node_id, source_handle FROM Edges WHERE source_node_id = ?', (finished_node_id,))
        except sqlite3.OperationalError:
            cursor.execute("SELECT target_node_id, 'default' FROM Edges WHERE source_node_id = ?", (finished_node_id,))
        targets = cursor.fetchall()
        for (target_node_id, source_handle) in targets:
            is_error_path = source_handle == 'error'
            if status == 'DONE' and is_error_path:
                continue
            if status == 'FAILED' and (not is_error_path):
                continue
            cursor.execute('SELECT source_node_id FROM Edges WHERE target_node_id = ?', (target_node_id,))
            dependencies = cursor.fetchall()
            all_met = True
            input_data_merged = {}
            for (dep_source_id,) in dependencies:
                cursor.execute("SELECT output_data, status FROM Jobs WHERE execution_id = ? AND node_id = ? AND status IN ('DONE', 'FAILED') ORDER BY finished_at DESC LIMIT 1", (execution_id, dep_source_id))
                row = cursor.fetchone()
                if not row:
                    all_met = False
                    break
                try:
                    prev_output = json.loads(row[0]) if row[0] else {}
                    if isinstance(prev_output, dict):
                        input_data_merged.update(prev_output)
                except:
                    pass
            if all_met:
                cursor.execute('SELECT 1 FROM Jobs WHERE execution_id = ? AND node_id = ?', (execution_id, target_node_id))
                if cursor.fetchone():
                    continue
                new_job_id = str(uuid.uuid4())
                user_id = hub.execution_user_cache.get(execution_id, 'system')
                cursor.execute('SELECT workflow_id FROM Jobs WHERE job_id = ?', (finished_job_id,))
                wf_row = cursor.fetchone()
                workflow_id = wf_row[0] if wf_row else None
                safe_input = json.dumps(input_data_merged, default=str)
                cursor.execute("INSERT INTO Jobs (job_id, execution_id, node_id, status, input_data, workflow_id, user_id) VALUES (?, ?, ?, 'PENDING', ?, ?, ?)", (new_job_id, execution_id, target_node_id, safe_input, workflow_id, user_id))
                conn.commit()
                hub.execute_sync('_publish_node_status', execution_id, target_node_id, 'RUNNING')
                job_event = Singleton.get_instance(multiprocessing.Event)
                if job_event:
                    job_event.set()
    except Exception as e:
        hub.logger.error(f'[Watchdog] Failed to queue downstream: {e}')

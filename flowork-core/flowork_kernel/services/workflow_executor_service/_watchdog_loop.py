########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\workflow_executor_service\_watchdog_loop.py total lines 50 
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
    hub.logger.info('[Watchdog] Started. Monitoring for stuck workflows...')
    while True:
        try:
            time.sleep(3)
            if not hub.db_service:
                continue
            conn = hub.db_service.create_connection()
            if not conn:
                continue
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT execution_id, user_id FROM Executions WHERE status = 'RUNNING'")
                running_execs = cursor.fetchall()
                for (exec_id, user_id) in running_execs:
                    if exec_id not in hub.execution_user_cache and user_id:
                        hub.execution_user_cache[exec_id] = user_id
                    cursor.execute("SELECT job_id, node_id, status FROM Jobs WHERE execution_id = ? AND status IN ('DONE', 'FAILED') ORDER BY finished_at DESC LIMIT 5", (exec_id,))
                    done_jobs = cursor.fetchall()
                    for (job_id, node_id, status) in done_jobs:
                        hub.execute_sync('_queue_downstream_nodes_sync', conn, exec_id, node_id, job_id, status)
            finally:
                conn.close()
        except Exception as e:
            hub.logger.error(f'[Watchdog] Error in loop: {e}')
            time.sleep(5)

########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\workflow_executor_service\_check_workflow_completion.py total lines 62 
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


async def run(hub, execution_id: str):
    if not hub.db_service:
        return
    conn = None
    try:
        query = "SELECT 1 FROM Jobs WHERE execution_id = ? AND status IN ('PENDING', 'RUNNING') LIMIT 1"
        conn = hub.db_service.create_connection()
        if not conn:
            return
        cursor = conn.cursor()
        cursor.execute(query, (execution_id,))
        pending_jobs = cursor.fetchone()
        if not pending_jobs:
            hub.logger.info(f'Workflow {execution_id} has no more pending jobs.')
            if await (await hub.execute_async('_handle_global_loop', execution_id, conn)):
                return
            hub.logger.info(f'Workflow {execution_id} finished. Generating report...')
            (outcome_report, analysis_report) = await hub.execute_async('_generate_r5_report', conn, execution_id)
            fail_query = "SELECT 1 FROM Jobs WHERE execution_id = ? AND status = 'FAILED' LIMIT 1"
            cursor.execute(fail_query, (execution_id,))
            has_failures = cursor.fetchone()
            final_status = 'FAILED' if has_failures else 'SUCCEEDED'
            try:
                cursor.execute('UPDATE Executions SET status = ?, finished_at = CURRENT_TIMESTAMP WHERE execution_id = ?', (final_status, execution_id))
                conn.commit()
                hub.logger.info(f'(DB FIX) Execution {execution_id} marked as {final_status} in DB.')
            except Exception as db_e:
                hub.logger.error(f'(DB FIX) Failed to update Execution status in DB: {db_e}')
            await hub.execute_async('_publish_workflow_status', execution_id, final_status, end_time=time.time(), outcome=outcome_report, analysis=analysis_report)
            hub.execution_user_cache.pop(execution_id, None)
            hub.execution_loop_cache.pop(execution_id, None)
        else:
            pass
    except Exception as e:
        hub.logger.error(f'Failed to check workflow completion for {execution_id}: {e}', exc_info=True)
    finally:
        if conn:
            conn.close()

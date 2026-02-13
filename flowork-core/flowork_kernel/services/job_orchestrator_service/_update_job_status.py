########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\job_orchestrator_service\_update_job_status.py total lines 30 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import sqlite3
import json
import time
import uuid
import threading
import traceback
import asyncio


def run(hub, job_id, status, error=None):
    with hub.db_lock:
        conn = sqlite3.connect(hub.db_path)
        cursor = conn.cursor()
        updates = ['status = ?', 'finished_at = ?' if status in ['COMPLETED', 'FAILED'] else 'started_at = ?']
        params = [status, time.time()]
        if error:
            updates.append('error_msg = ?')
            params.append(error)
        params.append(job_id)
        query = f"UPDATE global_jobs SET {', '.join(updates)} WHERE job_id = ?"
        cursor.execute(query, tuple(params))
        conn.commit()
        conn.close()

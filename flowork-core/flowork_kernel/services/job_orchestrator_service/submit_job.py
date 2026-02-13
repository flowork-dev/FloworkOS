########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\job_orchestrator_service\submit_job.py total lines 38 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import sqlite3
import time
import json
import uuid

def run(hub, *args, **kwargs):
    if len(args) < 2:
        job_type = kwargs.get('job_type', 'generic')
        payload = kwargs.get('payload', {})
    else:
        job_type = args[0]
        payload = args[1]

    job_id = str(uuid.uuid4())
    created_at = time.time()

    try:
        with hub.db_lock:
            conn = sqlite3.connect(hub.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO jobs (job_id, job_type, payload, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (job_id, job_type, json.dumps(payload), 'PENDING', created_at, created_at))
            conn.commit()
            conn.close()

        hub.logger.info(f"Job submitted: {job_id} [{job_type}]")
        return job_id
    except Exception as e:
        hub.logger.error(f"Error submitting job: {e}")
        return None

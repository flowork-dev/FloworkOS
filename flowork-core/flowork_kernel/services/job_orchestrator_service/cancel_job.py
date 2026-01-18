########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\job_orchestrator_service\cancel_job.py total lines 37 
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


def run(hub, job_id, user_id):
    """User bisa cancel job sendiri"""
    with hub.db_lock:
        conn = sqlite3.connect(hub.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, status FROM global_jobs WHERE job_id = ?', (job_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return {'success': False, 'error': 'Job not found'}
        (owner, status) = row
        if owner != user_id:
            conn.close()
            return {'success': False, 'error': 'Unauthorized'}
        if status in ['COMPLETED', 'FAILED', 'CANCELLED']:
            conn.close()
            return {'success': False, 'error': 'Job already finished'}
        cursor.execute("UPDATE global_jobs SET status = 'CANCELLED', finished_at = ? WHERE job_id = ?", (time.time(), job_id))
        conn.commit()
        conn.close()
        return {'success': True}

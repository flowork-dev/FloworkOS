########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\job_orchestrator_service\get_queue_list.py total lines 26 
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


def run(hub, limit=10):
    """Buat nampilin di GUI Dashboard"""
    with hub.db_lock:
        conn = sqlite3.connect(hub.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("\n                SELECT job_id, user_id, job_type, status, created_at, resource_req\n                FROM global_jobs\n                WHERE status IN ('QUEUED', 'RUNNING')\n                ORDER BY status DESC, priority DESC, created_at ASC\n                LIMIT ?\n            ", (limit,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

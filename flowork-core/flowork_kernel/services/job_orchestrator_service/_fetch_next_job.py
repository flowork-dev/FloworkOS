########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\job_orchestrator_service\_fetch_next_job.py total lines 27 
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


def run(hub):
    with hub.db_lock:
        conn = sqlite3.connect(hub.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("\n                SELECT * FROM global_jobs\n                WHERE status = 'QUEUED'\n                ORDER BY priority DESC, created_at ASC\n                LIMIT 1\n            ")
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
        return None

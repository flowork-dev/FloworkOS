########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\ai_provider_manager_service\_queue_worker_loop.py total lines 69 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import json
import importlib.util
import subprocess
import sys
import importlib.metadata
import tempfile
import zipfile
import shutil
import traceback
import time
import hashlib
import threading
import select
import asyncio
import uuid
import glob
from datetime import datetime
from aiohttp import web
from flowork_kernel.utils.file_helper import sanitize_filename


async def run(hub):
    """
        The FIFO Worker. Eats jobs one by one.
        """
    hub.logger.info('🚀 [Neural Queue] Worker Loop Started.')
    while True:
        try:
            job_id = await hub.job_queue.get()
            if job_id not in hub.active_jobs:
                hub.job_queue.task_done()
                continue
            job = hub.active_jobs[job_id]
            job['status'] = 'PROCESSING'
            job['started_at'] = time.time()
            session_id = job['payload'].get('session_id')
            if session_id:
                session = await hub.execute_async('get_session', session_id)
                if session:
                    session['active_job_id'] = job_id
                    session['active_job_status'] = 'PROCESSING'
                    await hub.execute_async('save_session', session_id, session)
            hub.logger.info(f"⚙️ [Neural Queue] Processing {job_id} ({job['type']})...")
            try:
                result = await (await hub.execute_async('_execute_job_logic', job))
                job['status'] = 'COMPLETED'
                job['result'] = result
            except Exception as e:
                hub.logger.error(f'❌ [Neural Queue] Job {job_id} Failed: {e}')
                job['status'] = 'FAILED'
                job['error'] = str(e)
            finally:
                job['completed_at'] = time.time()
                hub.job_queue.task_done()
                if session_id:
                    session = await hub.execute_async('get_session', session_id)
                    if session:
                        session['active_job_status'] = job['status']
                        await hub.execute_async('save_session', session_id, session)
        except Exception as e:
            hub.logger.error(f'🔥 [Neural Queue] Worker Loop Crash: {e}')
            await asyncio.sleep(1)

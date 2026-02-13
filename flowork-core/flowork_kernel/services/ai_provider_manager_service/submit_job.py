########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\ai_provider_manager_service\submit_job.py total lines 42 
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


async def run(hub, task_type, payload):
    """
        Main Entrypoint for Phase 2 API.
        Puts a job into the Async Queue.
        """
    if not hub.is_worker_running:
        asyncio.create_task(await hub.execute_async('_queue_worker_loop'))
        hub.is_worker_running = True
    job_id = f'job_{uuid.uuid4().hex[:8]}'
    job_data = {'id': job_id, 'type': task_type, 'payload': payload, 'status': 'QUEUED', 'submitted_at': time.time(), 'position': hub.job_queue.qsize() + 1}
    hub.active_jobs[job_id] = job_data
    await hub.job_queue.put(job_id)
    hub.logger.info(f"📥 [Neural Queue] Job {job_id} added. Position: {job_data['position']}")
    return job_data

########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\ai_provider_manager_service\_execute_job_logic.py total lines 44 
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


async def run(hub, job):
    """
        Router internal execution logic.
        """
    payload = job['payload']
    task_type = job['type']
    prompt = payload.get('prompt')
    endpoint_id = payload.get('endpoint_id')
    messages = payload.get('messages')
    stream = payload.get('stream', False)
    kwargs = payload.get('kwargs', {})
    if task_type == 'generation':
        loop = asyncio.get_event_loop()
        stream_override = False
        return await loop.run_in_executor(None, lambda : await hub.execute_async('query_ai_by_task', 'general', prompt, endpoint_id, messages, stream_override, **kwargs))
    return {'error': 'Unknown task type'}

########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\ai_provider_manager_service\_run_gguf.py total lines 47 
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


def run(hub, model_data, prompt, messages=None, stream=False):
    if not LLAMA_CPP_AVAILABLE:
        return {'error': 'llama-cpp-python not installed.'}
    path = model_data['full_path']
    worker = os.path.join(hub.kernel.project_root_path, 'flowork_kernel', 'workers', 'ai_worker.py')
    gpu = hub.loc.get_setting('ai_gpu_layers', 40)
    final_input = prompt
    if messages:
        final_input = hub.execute_sync('_construct_contextual_prompt', messages, prompt)
    cmd = [sys.executable, '-u', worker, path, str(gpu)]
    if stream:
        return hub.execute_sync('_stream_gguf_process', cmd, final_input)
    try:
        res = subprocess.run(cmd, input=final_input, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=1800)
        if res.returncode == 0:
            return {'type': 'text', 'data': res.stdout}
        return {'type': 'text', 'data': f'Error: {res.stderr}'}
    except Exception as e:
        return {'error': str(e)}

########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\ai_provider_manager_service\_run_audio_worker.py total lines 61 
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


def run(hub, model_data, prompt, **kwargs):
    path = model_data['full_path']
    worker = os.path.join(hub.kernel.project_root_path, 'flowork_kernel', 'workers', 'ai_worker.py')
    cmd = [sys.executable, '-u', worker, path]
    try:
        res = subprocess.run(cmd, input=prompt, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=300)
        if res.returncode != 0:
            hub.logger.error(f'[Audio Worker Fail] {res.stderr}')
            return {'error': f'Audio Gen Failed: {res.stderr}'}
        try:
            result = json.loads(res.stdout)
            if 'error' in result:
                return {'error': result['error']}
            if 'audio_path' in result:
                temp_path = result['audio_path']
                user_id = kwargs.get('user_id')
                if not user_id or user_id == 'None':
                    user_id = 'public'
                safe_user_id = sanitize_filename(user_id)
                user_dir = os.path.join(hub.audio_output_dir, safe_user_id)
                os.makedirs(user_dir, exist_ok=True)
                filename = os.path.basename(temp_path)
                final_path = os.path.join(user_dir, filename)
                if temp_path != final_path:
                    shutil.move(temp_path, final_path)
                safe_path_url = final_path.replace(os.sep, '/')
                url_with_engine = f'/api/v1/ai/files/view?path={safe_path_url}&engine_id={hub.engine_id}'
                return {'type': 'audio', 'data': final_path, 'url': url_with_engine}
            return {'type': 'json', 'data': result}
        except json.JSONDecodeError:
            return {'error': f'Invalid JSON from worker: {res.stdout}'}
    except Exception as e:
        return {'error': f'System Error: {str(e)}'}

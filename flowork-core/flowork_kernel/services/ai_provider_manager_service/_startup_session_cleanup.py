########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\ai_provider_manager_service\_startup_session_cleanup.py total lines 54 
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


def run(hub):
    """
        The Janitor: Scans all session files on startup.
        If any session says 'PROCESSING' (which means it crashed/died), set to 'CANCELLED'.
        """
    hub.logger.info('🧹 [The Janitor] Cleaning up zombie sessions...')
    try:
        session_files = glob.glob(os.path.join(hub.sessions_dir, '*.json'))
        count = 0
        for s_file in session_files:
            try:
                with open(s_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if data.get('active_job_status') in ['QUEUED', 'PROCESSING']:
                    data['active_job_status'] = 'CANCELLED'
                    data['active_job_id'] = None
                    data['messages'].append({'role': 'assistant', 'content': '⚠️ [System] Engine restarted. Previous task was cancelled.', 'timestamp': int(time.time() * 1000), 'error': True})
                    with open(s_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2)
                    count += 1
            except Exception as e:
                hub.logger.error(f'Failed to clean session {s_file}: {e}')
        if count > 0:
            hub.logger.warning(f'🧹 [The Janitor] Cleaned {count} zombie sessions.')
    except Exception as e:
        hub.logger.error(f'[The Janitor] Critical Error: {e}')

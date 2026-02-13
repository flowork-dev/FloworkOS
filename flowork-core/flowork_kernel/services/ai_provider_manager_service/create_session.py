########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\ai_provider_manager_service\create_session.py total lines 33 
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


def run(hub, title='New Chat', model_id=None):
    session_id = f'sess_{uuid.uuid4().hex[:12]}'
    session_data = {'id': session_id, 'title': title, 'modelId': model_id, 'created_at': int(time.time() * 1000), 'updated_at': int(time.time() * 1000), 'active_job_id': None, 'active_job_status': 'IDLE', 'messages': []}
    hub.execute_sync('save_session', session_id, session_data)
    return session_data

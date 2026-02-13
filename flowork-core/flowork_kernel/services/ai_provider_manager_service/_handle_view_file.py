########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\ai_provider_manager_service\_handle_view_file.py total lines 50 
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


async def run(hub, request):
    try:
        path = request.query.get('path')
        if not path:
            return web.Response(status=400, text='Missing path parameter')
        if '..' in path:
            return web.Response(status=403, text='Invalid path')
        if not os.path.exists(path):
            return web.Response(status=404, text='File not found')
        allowed_prefixes = [hub.image_output_dir, hub.audio_output_dir]
        abs_path = os.path.abspath(path)
        is_allowed = False
        for prefix in allowed_prefixes:
            if os.path.abspath(prefix) in abs_path:
                is_allowed = True
                break
        if '/generated_' not in abs_path and (not is_allowed):
            pass
        return web.FileResponse(abs_path)
    except Exception as e:
        hub.logger.error(f'File Serve Error: {e}')
        return web.Response(status=500, text=str(e))

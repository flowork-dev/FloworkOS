########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\system_routes\handle_clear_cache.py total lines 44 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import time
import os
import shutil
import threading
import json
from collections import Counter, defaultdict
from .base_api_route import BaseApiRoute
from aiohttp import web
import datetime
from flowork_kernel.exceptions import PermissionDeniedError


async def run(hub, request):
    try:
        (deleted_folders, deleted_files) = (0, 0)
        for (root, dirs, files) in os.walk(hub.kernel.project_root_path, topdown=False):
            if '__pycache__' in dirs:
                pycache_path = os.path.join(root, '__pycache__')
                try:
                    shutil.rmtree(pycache_path)
                    deleted_folders += 1
                except OSError:
                    pass
        data_folder = hub.kernel.data_path
        if os.path.isdir(data_folder):
            for filename in os.listdir(data_folder):
                if filename.endswith('.cache'):
                    try:
                        os.remove(os.path.join(data_folder, filename))
                        deleted_files += 1
                    except OSError:
                        pass
        summary = f'Cache clear complete. Removed {deleted_folders} folders and {deleted_files} cache files.'
        await hub.execute_async('logger', summary, 'SUCCESS')
        return await hub.execute_async('_json_response', {'status': 'success', 'message': summary}, status=200)
    except Exception as e:
        await hub.execute_async('logger', f'Clear cache via API failed: {e}', 'CRITICAL')
        return await hub.execute_async('_json_response', {'error': f'Internal server error during cache clearing: {e}'}, status=500)

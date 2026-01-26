########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\system_routes\handle_hot_reload.py total lines 25 
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
        hub.kernel.hot_reload_components()
        return await hub.execute_async('_json_response', {'status': 'success', 'message': 'Hot reload process initiated.'}, status=200)
    except Exception as e:
        await hub.execute_async('logger', f'Hot reload via API failed: {e}', 'CRITICAL')
        return await hub.execute_async('_json_response', {'error': f'Internal server error during hot reload: {e}'}, status=500)

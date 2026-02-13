########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\system_routes\handle_addon_upload.py total lines 30 
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
    app_service = hub.kernel.get_service('app_service')
    if not app_service:
        return await hub.execute_async('_json_response', {'error': 'App/Addon management service is not available.'}, status=503)
    body = await request.json()
    if body.get('bundle_data'):
        try:
            result = app_service.install_app_bundle(body.get('bundle_data'))
            return await hub.execute_async('_json_response', result)
        except Exception as inst_err:
            return await hub.execute_async('_json_response', {'error': str(inst_err)}, status=500)
    return await hub.execute_async('_json_response', {'error': 'Direct component upload deprecated. Use bundle installer.'}, status=410)

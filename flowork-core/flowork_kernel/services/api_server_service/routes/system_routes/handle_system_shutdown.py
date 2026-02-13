########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\system_routes\handle_system_shutdown.py total lines 32 
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
        permission_manager = hub.kernel.get_service('permission_manager_service', is_system_call=True)
        if permission_manager:
            permission_manager.check_permission('engine_management')
        await hub.execute_async('logger', 'API request received to shut down the engine.', 'CRITICAL', 'ApiServer')
        await hub.kernel.shutdown_application()
        return await hub.execute_async('_json_response', {'status': 'accepted', 'message': 'Engine shutdown process initiated.'}, status=202)
    except PermissionDeniedError as e:
        await hub.execute_async('logger', f'Permission denied for engine shutdown: {e}', 'CRITICAL', 'ApiServer')
        return await hub.execute_async('_json_response', {'error': str(e)}, status=403)
    except Exception as e:
        await hub.execute_async('logger', f'Error during engine shutdown request: {e}', 'CRITICAL', 'ApiServer')
        return await hub.execute_async('_json_response', {'error': 'Internal server error during shutdown.'}, status=500)

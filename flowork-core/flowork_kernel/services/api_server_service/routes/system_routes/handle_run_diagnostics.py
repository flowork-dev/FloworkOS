########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\system_routes\handle_run_diagnostics.py total lines 37 
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
    """
        Handles the request to run system diagnostics/scanners.
        Payload: { "scan_id": "optional_id", "target_scanner_id": "optional_scanner_key" }
        """
    try:
        body = await request.json()
        scan_id = body.get('scan_id', f'SCAN-{int(time.time())}')
        target_scanner_id = body.get('target_scanner_id')
        app_service = hub.kernel.get_service('app_service')
        diag_app = app_service.get_instance('apps', 'system_doctor') if app_service else None
        if not diag_app:
            return await hub.execute_async('_json_response', {'error': 'Diagnostics App (system_doctor) is not installed or available.'}, status=503)
        await hub.execute_async('logger', f'Diagnostics requested via App. ID: {scan_id}, Target: {target_scanner_id}', 'INFO')
        result = diag_app.start_scan_headless(scan_id, target_scanner_id)
        return await hub.execute_async('_json_response', result, status=200)
    except Exception as e:
        await hub.execute_async('logger', f'Failed to execute diagnostics: {e}', 'ERROR')
        return await hub.execute_async('_json_response', {'error': str(e)}, status=500)

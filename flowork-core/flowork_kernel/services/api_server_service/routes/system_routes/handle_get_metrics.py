########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\system_routes\handle_get_metrics.py total lines 24 
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
    metrics_service = hub.service_instance.metrics_service
    if not metrics_service:
        return await hub.execute_async('_json_response', {'error': 'Metrics service is not available.'}, status=503)
    metrics_data = metrics_service.serve_metrics()
    return web.Response(body=metrics_data, content_type='text/plain; version=0.0.4')

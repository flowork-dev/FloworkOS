########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\component_routes\handle_run_component.py total lines 32 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from .base_api_route import BaseApiRoute
import os
import json
import mimetypes
import zipfile
import io
import base64
import shutil
import asyncio
from aiohttp import web
import threading


async def run(hub, request):
    """
        Endpoint untuk menjalankan komponen secara langsung (Standalone Execution).
        """
    try:
        body = await request.json()
        executor = hub.service_instance.kernel.get_service('workflow_executor_service')
        if not executor:
            return await hub.execute_async('_json_response', {'error': 'Workflow Executor Service unavailable.'}, status=503)
        await executor.execute_standalone_node(body)
        return await hub.execute_async('_json_response', {'status': 'success', 'message': 'Execution started.'})
    except Exception as e:
        return await hub.execute_async('_json_response', {'error': str(e)}, status=500)

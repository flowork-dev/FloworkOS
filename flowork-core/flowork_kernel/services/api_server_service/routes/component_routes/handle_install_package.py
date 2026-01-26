########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\component_routes\handle_install_package.py total lines 34 
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
    try:
        body = await request.json()
        comp_id = body.get('id')
        zip_b64 = body.get('zip_data')
        if not comp_id or not zip_b64:
            return await hub.execute_async('_json_response', {'error': "Missing 'id' or 'zip_data'."}, status=400)
        target_dir = os.path.join(hub.kernel.project_root_path, '..', 'app', comp_id)
        os.makedirs(target_dir, exist_ok=True)
        zip_bytes = base64.b64decode(zip_b64)
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            zf.extractall(target_dir)
        return await hub.execute_async('_json_response', {'id': comp_id, 'status': 'success'})
    except Exception as e:
        return await hub.execute_async('_json_response', {'error': str(e)}, status=500)

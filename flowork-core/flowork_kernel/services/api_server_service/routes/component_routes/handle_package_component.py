########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\component_routes\handle_package_component.py total lines 40 
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
        if not comp_id:
            return await hub.execute_async('_json_response', {'error': "Missing 'id'."}, status=400)
        app_service = hub.service_instance.kernel.get_service('app_service')
        item_data = app_service.registry['apps']['data'].get(comp_id)
        if not item_data:
            return await hub.execute_async('_json_response', {'error': f"Component '{comp_id}' not found."}, status=404)
        folder_path = item_data.get('path')
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for (root, dirs, files) in os.walk(folder_path):
                dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', '.venv']]
                for file in files:
                    file_path = os.path.join(root, file)
                    zip_file.write(file_path, os.path.relpath(file_path, folder_path))
        return await hub.execute_async('_json_response', {'id': comp_id, 'zip_data': base64.b64encode(buffer.getvalue()).decode('utf-8')})
    except Exception as e:
        return await hub.execute_async('_json_response', {'error': str(e)}, status=500)

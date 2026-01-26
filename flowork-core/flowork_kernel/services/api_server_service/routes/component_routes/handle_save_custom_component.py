########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\component_routes\handle_save_custom_component.py total lines 46 
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
        Saves a custom component from Component Forge to disk.
        """
    try:
        body = await request.json()
        comp_id = body.get('id')
        code_content = body.get('code', '')
        manifest_content = body.get('manifest', {})
        if not comp_id or not code_content:
            return await hub.execute_async('_json_response', {'error': "Missing 'id' or 'code'."}, status=400)
        root_path = os.path.abspath(os.path.join(hub.kernel.project_root_path, '..', 'app'))
        comp_dir = os.path.join(root_path, comp_id)
        os.makedirs(comp_dir, exist_ok=True)
        entry_point = manifest_content.get('entry_point', 'backend/node.py')
        entry_path = os.path.join(comp_dir, entry_point)
        os.makedirs(os.path.dirname(entry_path), exist_ok=True)
        with open(entry_path, 'w', encoding='utf-8') as f:
            f.write(code_content)
        with open(os.path.join(comp_dir, 'manifest.json'), 'w', encoding='utf-8') as f:
            json.dump(manifest_content, f, indent=4)
        app_service = hub.service_instance.kernel.get_service('app_service')
        if app_service:
            threading.Thread(target=app_service.sync, args=('apps',)).start()
        return await hub.execute_async('_json_response', {'status': 'success', 'message': f'Component {comp_id} saved.'})
    except Exception as e:
        return await hub.execute_async('_json_response', {'error': str(e)}, status=500)

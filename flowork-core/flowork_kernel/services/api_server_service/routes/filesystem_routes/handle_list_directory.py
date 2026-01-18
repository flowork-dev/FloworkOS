########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\filesystem_routes\handle_list_directory.py total lines 41 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import sys
import json
import mimetypes
from urllib.parse import urlparse, parse_qs
from .base_api_route import BaseApiRoute
from aiohttp import web


async def run(hub, request):
    safe_roots = await hub.execute_async('_get_safe_roots')
    req_path = request.query.get('path', '')
    if not req_path:
        target_path = os.path.abspath(hub.kernel.project_root_path)
    else:
        target_path = os.path.abspath(req_path)
    target_path = os.path.normpath(target_path)
    is_safe = any((target_path.startswith(os.path.normpath(root)) for root in safe_roots))
    if target_path.startswith('/app/data') or 'generated_images' in target_path:
        is_safe = True
    if not is_safe:
        await hub.execute_async('logger', f'Forbidden path access attempt: {target_path}', 'CRITICAL')
        return await hub.execute_async('_json_response', {'error': 'Access to the requested path is forbidden.'}, status=403)
    try:
        if not os.path.isdir(target_path):
            return await hub.execute_async('_json_response', {'error': f'Path is not a valid directory: {target_path}'}, status=400)
        items = []
        for item_name in sorted(os.listdir(target_path), key=lambda s: s.lower()):
            item_path = os.path.join(target_path, item_name)
            is_dir = os.path.isdir(item_path)
            items.append({'name': item_name, 'type': 'directory' if is_dir else 'file', 'path': os.path.abspath(item_path).replace(os.sep, '/')})
        return await hub.execute_async('_json_response', items)
    except Exception as e:
        await hub.execute_async('logger', f"Error listing directory '{target_path}': {str(e)}", 'ERROR')
        return await hub.execute_async('_json_response', {'error': str(e)}, status=500)

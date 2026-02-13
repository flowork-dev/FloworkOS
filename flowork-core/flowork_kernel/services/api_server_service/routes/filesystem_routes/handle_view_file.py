########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\filesystem_routes\handle_view_file.py total lines 38 
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
    file_path = request.query.get('path')
    if not file_path:
        return await hub.execute_async('_json_response', {'error': "Missing 'path' parameter."}, status=400)
    target_path = os.path.abspath(file_path)
    if not os.path.exists(target_path):
        return await hub.execute_async('_json_response', {'error': 'File not found.'}, status=404)
    if not os.path.isfile(target_path):
        return await hub.execute_async('_json_response', {'error': 'Path is not a file.'}, status=400)
    allowed_prefixes = [os.path.abspath(hub.kernel.project_root_path), os.path.abspath(hub.kernel.data_path), '/app/data']
    allowed_prefixes.extend(await hub.execute_async('_get_safe_roots'))
    is_safe = any((target_path.startswith(p) for p in allowed_prefixes))
    if not is_safe:
        await hub.execute_async('logger', f'Blocked access to file outside safe scope: {target_path}', 'WARN')
        return await hub.execute_async('_json_response', {'error': 'Access denied.'}, status=403)
    try:
        (mime_type, _) = mimetypes.guess_type(target_path)
        if mime_type is None:
            mime_type = 'application/octet-stream'
        return web.FileResponse(target_path, headers={'Content-Type': mime_type})
    except Exception as e:
        await hub.execute_async('logger', f"Error serving file '{target_path}': {e}", 'ERROR')
        return await hub.execute_async('_json_response', {'error': str(e)}, status=500)

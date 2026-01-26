########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\routes\filesystem_routes\handle_list_directory.py total lines 38 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import sys
import json
from urllib.parse import urlparse, parse_qs
from .base_api_route import BaseApiRoute


def run(hub, handler):
    safe_roots = hub.execute_sync('_get_safe_roots')
    query_components = parse_qs(urlparse(handler.path).query)
    req_path = query_components.get('path', [''])[0]
    if not req_path:
        target_path = os.path.abspath(hub.kernel.project_root_path)
    else:
        target_path = os.path.abspath(req_path)
    target_path = os.path.normpath(target_path)
    is_safe = any((target_path.startswith(os.path.normpath(root)) for root in safe_roots))
    if not is_safe:
        hub.execute_sync('logger', f'Forbidden path access attempt: {target_path}', 'CRITICAL')
        return handler._send_response(403, {'error': 'Access to the requested path is forbidden.'})
    try:
        if not os.path.isdir(target_path):
            return handler._send_response(400, {'error': f'Path is not a valid directory: {target_path}'})
        items = []
        for item_name in sorted(os.listdir(target_path), key=lambda s: s.lower()):
            item_path = os.path.join(target_path, item_name)
            is_dir = os.path.isdir(item_path)
            items.append({'name': item_name, 'type': 'directory' if is_dir else 'file', 'path': os.path.abspath(item_path).replace(os.sep, '/')})
        handler._send_response(200, items)
    except Exception as e:
        hub.execute_sync('logger', f"Error listing directory '{target_path}': {str(e)}", 'ERROR')
        handler._send_response(500, {'error': str(e)})

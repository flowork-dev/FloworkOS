########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\filesystem_routes\handle_list_drives.py total lines 32 
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
    try:
        safe_roots = await hub.execute_async('_get_safe_roots')
        drives_info = []
        for path in safe_roots:
            name = path
            user_home = os.path.expanduser('~')
            if path.startswith(user_home):
                relative_part = os.path.relpath(path, user_home)
                if relative_part == '.':
                    name = 'User Home'
                else:
                    name = f'My {relative_part}'
            drives_info.append({'name': name, 'path': path.replace(os.sep, '/')})
        return await hub.execute_async('_json_response', drives_info)
    except Exception as e:
        return await hub.execute_async('_json_response', {'error': f'Could not list drives: {str(e)}'}, status=500)

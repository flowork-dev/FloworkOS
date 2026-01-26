########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\routes\filesystem_routes\handle_list_drives.py total lines 30 
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
    try:
        safe_roots = hub.execute_sync('_get_safe_roots')
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
        handler._send_response(200, drives_info)
    except Exception as e:
        handler._send_response(500, {'error': f'Could not list drives: {str(e)}'})

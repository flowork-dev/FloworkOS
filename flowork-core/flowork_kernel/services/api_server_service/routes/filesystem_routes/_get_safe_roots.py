########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\filesystem_routes\_get_safe_roots.py total lines 46 
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


def run(hub):
    roots = [os.path.abspath(hub.kernel.project_root_path)]
    if hasattr(hub.kernel, 'data_path'):
        roots.append(os.path.abspath(hub.kernel.data_path))
    browseable_paths_config = os.path.join(hub.kernel.data_path, 'browseable_paths.json')
    try:
        if os.path.exists(browseable_paths_config):
            with open(browseable_paths_config, 'r', encoding='utf-8') as f:
                user_defined_paths = json.load(f)
                if isinstance(user_defined_paths, list):
                    for path in user_defined_paths:
                        if os.path.isdir(path):
                            roots.append(os.path.abspath(path))
    except Exception as e:
        hub.execute_sync('logger', f"Could not load or parse 'browseable_paths.json': {e}", 'WARN')
    user_home = os.path.expanduser('~')
    common_dirs = ['Desktop', 'Documents', 'Downloads', 'Pictures', 'Music', 'Videos']
    for d in common_dirs:
        path = os.path.join(user_home, d)
        if os.path.isdir(path):
            roots.append(os.path.abspath(path))
    if PSUTIL_AVAILABLE:
        for partition in psutil.disk_partitions():
            roots.append(os.path.abspath(partition.mountpoint))
    elif sys.platform == 'win32':
        import string
        for letter in string.ascii_uppercase:
            drive = f'{letter}:\\'
            if os.path.isdir(drive):
                roots.append(drive)
    return sorted(list(set(roots)))

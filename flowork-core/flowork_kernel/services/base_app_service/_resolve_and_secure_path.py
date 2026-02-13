########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\base_app_service\_resolve_and_secure_path.py total lines 23 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import shutil
from pathlib import Path


def run(hub, path_str, user_id):
    if path_str:
        clean_path = str(path_str).replace('\\', '/')
        if '/users/system' in clean_path and user_id and (user_id != 'system'):
            clean_path = clean_path.replace('/users/system', f'/users/{user_id}')
        user_prefix_detect = f'/users/{user_id}'
        if user_prefix_detect in clean_path:
            parts = clean_path.split(user_prefix_detect, 1)
            if len(parts) > 1:
                clean_path = parts[1].lstrip('/')
        path_str = clean_path.lstrip('/')
    return super()._resolve_and_secure_path(path_str, user_id)

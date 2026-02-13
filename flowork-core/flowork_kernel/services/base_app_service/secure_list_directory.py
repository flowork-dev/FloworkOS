########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\base_app_service\secure_list_directory.py total lines 19 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import shutil
from pathlib import Path


def run(hub, path, user_id):
    """[App Path] Overrides Node listing to provide Virtual Paths."""
    res = super().secure_list_directory(path, user_id)
    if res.get('status') == 'success':
        res['current_path'] = hub.execute_sync('_to_virtual_path', res['current_path'])
        for item in res['items']:
            item['path'] = hub.execute_sync('_to_virtual_path', item.get('physical_path') or item.get('path'))
    return res

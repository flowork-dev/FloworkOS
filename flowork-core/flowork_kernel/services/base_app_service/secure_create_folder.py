########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\base_app_service\secure_create_folder.py total lines 17 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import shutil
from pathlib import Path


def run(hub, current_path, name, user_id):
    """[App Path] Returns Virtual Path of the new folder."""
    res = super().secure_create_folder(current_path, name, user_id)
    if res.get('status') == 'success':
        res['path'] = hub.execute_sync('_to_virtual_path', res.get('physical_path') or res.get('path'))
    return res

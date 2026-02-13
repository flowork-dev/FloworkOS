########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\base_app_service\_to_virtual_path.py total lines 20 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import shutil
from pathlib import Path


def run(hub, physical_path):
    """[English Note] Translates server paths to GUI-friendly /app/data/."""
    from flowork_kernel.utils.path_helper import get_data_directory
    data_dir = str(get_data_directory())
    p_str = str(physical_path)
    if p_str.startswith(data_dir):
        rel = p_str[len(data_dir):].replace('\\', '/').lstrip('/')
        return f'/app/data/{rel}'
    return p_str.replace('\\', '/')

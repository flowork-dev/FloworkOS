########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\state_manager_service\_load_global_state.py total lines 22 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import json
import shutil
import threading
from collections import OrderedDict


def run(hub):
    try:
        if os.path.exists(hub.global_state_file_path):
            with open(hub.global_state_file_path, 'r', encoding='utf-8') as f:
                hub._global_state_cache = json.load(f)
        else:
            hub._global_state_cache = {}
    except:
        hub._global_state_cache = {}

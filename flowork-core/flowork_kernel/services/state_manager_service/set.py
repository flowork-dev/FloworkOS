########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\state_manager_service\set.py total lines 23 
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


def run(hub, key, value, user_id: str=None):
    with hub._lock:
        if user_id:
            if user_id not in hub._user_state_cache:
                hub._user_state_cache[user_id] = hub.execute_sync('_load_user_state_from_file', user_id)
            hub._user_state_cache[user_id][key] = value
            hub.execute_sync('_save_user_state_to_file', user_id, self._user_state_cache[user_id])
        else:
            hub._global_state_cache[key] = value
            hub.execute_sync('_save_global_state')

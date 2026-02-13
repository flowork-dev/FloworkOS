########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\state_manager_service\_save_user_state_to_file.py total lines 16 
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


def run(hub, user_id: str, state_data: dict):
    state_file_path = hub.execute_sync('_get_user_state_path', user_id)
    hub.execute_sync('_atomic_write', state_file_path, state_data)

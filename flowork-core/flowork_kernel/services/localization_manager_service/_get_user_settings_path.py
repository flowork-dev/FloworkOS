########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\localization_manager_service\_get_user_settings_path.py total lines 17 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import json
from collections import OrderedDict


def run(hub, user_id: str):
    if not user_id:
        return os.path.join(hub.kernel.data_path, hub.SETTINGS_FILE)
    user_dir = os.path.join(hub.users_data_path, user_id)
    os.makedirs(user_dir, exist_ok=True)
    return os.path.join(user_dir, hub.SETTINGS_FILE)

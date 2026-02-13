########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\localization_manager_service\_save_settings.py total lines 20 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import json
from collections import OrderedDict


def run(hub, settings_to_save, user_id=None):
    settings_file_path = hub.execute_sync('_get_user_settings_path', user_id)
    try:
        with open(settings_file_path, 'w', encoding='utf-8') as f:
            json.dump(settings_to_save, f, indent=4)
        if user_id in hub._settings_cache:
            hub._settings_cache[user_id] = settings_to_save
    except Exception as e:
        hub.kernel.write_to_log(f"LocalizationManager: Failed to save settings for user '{user_id}': {e}", 'ERROR')

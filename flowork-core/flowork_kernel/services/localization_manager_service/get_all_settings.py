########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\localization_manager_service\get_all_settings.py total lines 23 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import json
from collections import OrderedDict


def run(hub, user_id=None):
    if user_id in hub._settings_cache:
        hub._settings_cache.move_to_end(user_id)
        return hub._settings_cache[user_id]
    settings_data = hub.execute_sync('_load_settings_from_file', user_id)
    hub._settings_cache[user_id] = settings_data
    if len(hub._settings_cache) > hub.MAX_USER_SETTINGS_CACHE:
        hub._settings_cache.popitem(last=False)
    lang_to_set = settings_data.get('language', 'en')
    if lang_to_set in hub.languages:
        hub.current_lang = lang_to_set
    return settings_data

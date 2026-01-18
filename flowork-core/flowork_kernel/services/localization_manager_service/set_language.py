########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\localization_manager_service\set_language.py total lines 19 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import json
from collections import OrderedDict


def run(hub, lang_id, user_id=None):
    if lang_id in hub.languages:
        hub.current_lang = lang_id
        hub.execute_sync('save_setting', 'language', lang_id, user_id=user_id)
        hub.kernel.write_to_log(f"LocalizationManager: Language for user '{user_id}' set to '{lang_id}'.", 'INFO')
        return True
    hub.kernel.write_to_log(f"LocalizationManager: Language '{lang_id}' not found.", 'WARN')
    return False

########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\localization_manager_service\_merge_from_directory.py total lines 28 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import json
from collections import OrderedDict


def run(hub, directory_path, source_name='base'):
    if os.path.isdir(directory_path):
        for filename in os.listdir(directory_path):
            if filename.endswith('.json'):
                lang_id = os.path.splitext(filename)[0]
                filepath = os.path.join(directory_path, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        lang_data = json.load(f)
                        if lang_id not in hub.languages:
                            hub.languages[lang_id] = {}
                        for (key, value) in lang_data.items():
                            if key in hub.languages[lang_id] and source_name != 'base':
                                hub.execute_sync('logger', f"Duplicate locale key '{key}' found from '{source_name}'. Overwriting.", 'WARN')
                            hub.languages[lang_id][key] = value
                except Exception as e:
                    hub.kernel.write_to_log(f"Failed to merge language '{lang_id}' from '{source_name}' at {filepath}: {e}", 'ERROR')

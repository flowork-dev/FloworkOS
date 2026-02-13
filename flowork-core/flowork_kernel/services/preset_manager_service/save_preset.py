########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\preset_manager_service\save_preset.py total lines 34 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import json
import shutil
import datetime
import threading
from flowork_kernel.exceptions import PresetNotFoundError
from flowork_kernel.utils.flowchain_verifier import verify_workflow_chain, calculate_hash
from flowork_kernel.services.database_service.database_service import DatabaseService
from flowork_kernel.singleton import Singleton
import logging


def run(hub, name: str, workflow_data: dict, user_id: str, signature: str, public_address: str=None) -> bool:
    if not name or not user_id:
        return False
    wf_path = hub.execute_sync('_get_preset_workflow_path', user_id, name)
    os.makedirs(wf_path, exist_ok=True)
    with hub._save_lock:
        (_, last_ver) = hub.execute_sync('_get_latest_version_file', wf_path)
        ver = last_ver + 1
        ts = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        fname = f'v{ver}_{ts}.json'
        payload = {'version': ver, 'timestamp': ts, 'author_id': public_address or user_id, 'workflow_data': workflow_data, 'signature': signature}
        with open(os.path.join(wf_path, fname), 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2)
        hub.execute_sync('_sync_trigger_rules_for_preset', name, workflow_data, user_id)
        hub.logger.info(f"Preset '{name}' saved (v{ver}).")
        return True

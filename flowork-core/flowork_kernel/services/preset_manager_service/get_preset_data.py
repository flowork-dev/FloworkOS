########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\preset_manager_service\get_preset_data.py total lines 28 
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


def run(hub, name: str, user_id: str):
    wf_path = hub.execute_sync('_get_preset_workflow_path', user_id, name)
    (file_path, _) = hub.execute_sync('_get_latest_version_file', wf_path)
    if not file_path:
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f).get('workflow_data')
    except:
        return None

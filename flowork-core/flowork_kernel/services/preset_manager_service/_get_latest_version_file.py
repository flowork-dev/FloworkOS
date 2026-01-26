########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\preset_manager_service\_get_latest_version_file.py total lines 27 
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


def run(hub, workflow_path: str):
    if not os.path.isdir(workflow_path):
        return (None, 0)
    files = [f for f in os.listdir(workflow_path) if f.endswith('.json') and f.startswith('v')]
    if not files:
        return (None, 0)
    latest = max(files, key=lambda x: int(x.split('_')[0][1:]) if x.split('_')[0][1:].isdigit() else 0)
    version = int(latest.split('_')[0][1:]) if latest.split('_')[0][1:].isdigit() else 0
    return (os.path.join(workflow_path, latest), version)

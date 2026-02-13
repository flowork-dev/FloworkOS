########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\preset_manager_service\_get_user_presets_path.py total lines 24 
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


def run(hub, user_id: str):
    target_user = user_id if user_id else '_global'
    path = os.path.join(hub.users_data_path, target_user, 'presets')
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
    return path

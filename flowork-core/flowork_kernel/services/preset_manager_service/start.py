########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\preset_manager_service\start.py total lines 24 
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


def run(hub):
    hub.trigger_manager = hub.kernel.get_service('app_service')
    hub.db_service = Singleton.get_instance(DatabaseService)
    if not hub.db_service:
        hub.logger.critical('CRITICAL: DatabaseService missing.')
    os.makedirs(hub.users_data_path, exist_ok=True)

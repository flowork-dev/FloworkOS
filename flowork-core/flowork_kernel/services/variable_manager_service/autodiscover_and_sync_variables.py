########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\variable_manager_service\autodiscover_and_sync_variables.py total lines 34 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import json
import threading
import base64
import logging
import secrets
import string
import random
import sqlite3
from collections import OrderedDict
from flowork_kernel.exceptions import PermissionDeniedError


def run(hub):
    """
        [REPAIR] Ensures all global keys appear in the UI.
        If not in Environment, creates a placeholder in DB.
        """
    for key in hub.SYSTEM_GLOBAL_KEYS:
        env_val = os.environ.get(key)
        existing = hub.execute_sync('get_variable_metadata', key, user_id=None)
        if not existing:
            if env_val:
                hub.kernel.write_to_log(f'[AutoSync] Injecting {key} from Environment to DB', 'INFO')
                hub.execute_sync('set_variable', key, env_val, is_secret=True, is_enabled=True, mode='single', user_id=None)
            else:
                hub.kernel.write_to_log(f'[AutoSync] Seeding UI placeholder for system key: {key}', 'DEBUG')
                hub.execute_sync('set_variable', key, 'PLEASE_EDIT_ME', is_secret=True, is_enabled=True, mode='single', user_id=None)

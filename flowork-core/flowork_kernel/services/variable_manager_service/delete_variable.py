########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\variable_manager_service\delete_variable.py total lines 39 
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


def run(hub, name, user_id: str):
    if name in hub.SYSTEM_GLOBAL_KEYS:
        return False
    conn = hub.execute_sync('_get_db_connection')
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        if user_id:
            cursor.execute('DELETE FROM Variables WHERE user_id = ? AND name = ?', (user_id, name))
        else:
            cursor.execute('DELETE FROM Variables WHERE user_id IS NULL AND name = ?', (name,))
        conn.commit()
        with hub._lock:
            hub._variables_data_cache.clear()
        return True
    except:
        return False
    finally:
        conn.close()

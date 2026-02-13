########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\variable_manager_service\get_variable_metadata.py total lines 46 
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


def run(hub, name, user_id: str=None):
    conn = hub.execute_sync('_get_db_connection')
    if not conn:
        return None
    try:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        target_data = None
        if user_id:
            cursor.execute('SELECT * FROM Variables WHERE user_id = ? AND name = ?', (user_id, name))
            target_data = cursor.fetchone()
        if not target_data:
            cursor.execute('SELECT * FROM Variables WHERE user_id IS NULL AND name = ?', (name,))
            target_data = cursor.fetchone()
        if not target_data:
            return None
        val = target_data['value']
        try:
            val_parsed = json.loads(val)
        except:
            val_parsed = val
        return {'name': target_data['name'], 'value': val_parsed, 'is_secret': bool(target_data['is_secret']), 'is_enabled': bool(target_data['is_enabled']), 'mode': target_data['mode'], 'is_protected': target_data['name'] in hub.SYSTEM_GLOBAL_KEYS}
    except Exception as e:
        hub.kernel.write_to_log(f'[VariableManager] Get Metadata Error for {name}: {e}', 'ERROR')
        return None
    finally:
        conn.close()

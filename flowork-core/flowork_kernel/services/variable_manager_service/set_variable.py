########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\variable_manager_service\set_variable.py total lines 75 
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
import sqlite3

def run(hub, name, value, is_secret, is_enabled=True, mode='single', user_id: str=None):
    """
    Saves or updates a neural variable with SQL Elite protection.
    Optimized for Parallel Million-User writes and Atomic Integrity.
    """
    if name in hub.SYSTEM_GLOBAL_KEYS:
        user_id = None

    try:
        with hub.execute_sync('transaction') as conn:
            cursor = conn.cursor()
            db_value = value
            is_already_encoded = False

            if is_secret and (db_value == '' or db_value is None):
                if user_id:
                    cursor.execute('SELECT value FROM Variables WHERE user_id = ? AND name = ?', (user_id, name))
                else:
                    cursor.execute('SELECT value FROM Variables WHERE user_id IS NULL AND name = ?', (name,))

                existing_row = cursor.fetchone()
                if existing_row and existing_row[0]:
                    db_value = existing_row[0]
                    is_already_encoded = True

            if not is_already_encoded:
                if isinstance(db_value, (dict, list)):
                    db_value = json.dumps(db_value)
                else:
                    if is_secret and db_value and (db_value != 'PLEASE_EDIT_ME'):
                        try:
                            db_value = base64.b64encode(str(db_value).encode('utf-8')).decode('utf-8')
                        except:
                            db_value = str(db_value)
                    db_value = str(db_value)

            if name in hub.SYSTEM_GLOBAL_KEYS:
                cursor.execute('DELETE FROM Variables WHERE user_id IS NULL AND name = ?', (name,))

            query = '''
                INSERT INTO Variables (user_id, name, value, is_secret, is_enabled, mode)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id, name) DO UPDATE SET
                    value=excluded.value,
                    is_secret=excluded.is_secret,
                    is_enabled=excluded.is_enabled,
                    mode=excluded.mode
            '''
            cursor.execute(query, (user_id, name, db_value, 1 if is_secret else 0, 1 if is_enabled else 0, mode))

    except Exception as e:
        hub.logger.error(f'❌ [VariableManager] Save Failed for {name}: {e}')
        return False

    cache_key = f'{user_id}_{name}'
    with hub._lock:
        if cache_key in hub._variables_data_cache:
            del hub._variables_data_cache[cache_key]
        hub._sequential_counters.pop(cache_key, None)

    hub.logger.info(f"✅ [VariableManager] Variable '{name}' ingested successfully.")
    return True

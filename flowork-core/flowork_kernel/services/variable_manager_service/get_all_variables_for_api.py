########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\variable_manager_service\get_all_variables_for_api.py total lines 82 
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


def run(hub, user_id: str):
    """
    Fetches all variables for GUI/API display.
    Optimized with SQL Elite for Million-User dashboard concurrency.
    Protects secrets by masking them before exposure.
    """
    conn = hub.execute_sync('create_connection')
    if not conn:
        return []

    try:
        cursor = conn.cursor()

        if user_id:
            query = 'SELECT * FROM Variables WHERE user_id = ? OR user_id IS NULL ORDER BY name ASC'
            cursor.execute(query, (user_id,))
        else:
            query = 'SELECT * FROM Variables WHERE user_id IS NULL ORDER BY name ASC'
            cursor.execute(query)

        rows = cursor.fetchall()
        result = []
        seen = set()

        for row in rows:
            if row['name'] in seen:
                continue
            seen.add(row['name'])

            val = row['value']
            try:
                val_parsed = json.loads(val)
            except:
                val_parsed = val

            is_secret = bool(row['is_secret'])
            final_value = val_parsed

            if is_secret and isinstance(final_value, str):
                final_value = ''

            if row['mode'] in ['random', 'sequential'] and (not isinstance(final_value, list)):
                if isinstance(final_value, str) and final_value:
                    final_value = [final_value]
                else:
                    final_value = []

            result.append({
                'name': row['name'],
                'value': final_value,
                'is_secret': is_secret,
                'is_enabled': bool(row['is_enabled']),
                'mode': row['mode'],
                'is_protected': row['name'] in hub.SYSTEM_GLOBAL_KEYS
            })

        return result

    except Exception as e:
        hub.logger.error(f'❌ [VariableManager] API discovery failed: {e}')
        return []
    finally:
        conn.close()

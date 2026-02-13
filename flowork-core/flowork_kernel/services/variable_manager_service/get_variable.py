########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\variable_manager_service\get_variable.py total lines 106 
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
    """
    Retrieves a variable value with Neural Vault Protection.
    Optimized for Million-User access and Robot-Brain security.
    """
    cache_key = f'{user_id}_{name}'
    cached_val = None

    with hub._lock:
        if cache_key in hub._variables_data_cache:
            cached_val = hub._variables_data_cache[cache_key]

    if cached_val is None:
        conn = hub.execute_sync('create_connection')
        if not conn:
            return None

        try:
            cursor = conn.cursor()
            target_data = None

            if user_id:
                cursor.execute('SELECT * FROM Variables WHERE user_id = ? AND name = ? AND is_enabled = 1', (user_id, name))
                target_data = cursor.fetchone()

            if not target_data:
                cursor.execute('SELECT * FROM Variables WHERE user_id IS NULL AND name = ? AND is_enabled = 1', (name,))
                target_data = cursor.fetchone()

            if not target_data:
                return None

            raw_val = target_data['value']
            mode = target_data['mode']
            is_secret = bool(target_data['is_secret'])
            parsed_val = raw_val

            try:
                parsed_json = json.loads(raw_val)
                parsed_val = parsed_json
            except:
                pass

            if is_secret and isinstance(parsed_val, str):
                try:
                    decoded = base64.b64decode(str(parsed_val).encode('utf-8')).decode('utf-8')
                    if all((c in string.printable for c in decoded)):
                        parsed_val = decoded
                except:
                    pass

            cached_val = {'value': parsed_val, 'mode': mode}

            with hub._lock:
                if len(hub._variables_data_cache) > 5000:
                    hub._variables_data_cache.popitem(last=False) # Evict data paling lama
                hub._variables_data_cache[cache_key] = cached_val

        except Exception as e:
            hub.logger.error(f'❌ [VariableManager] Neural Link Error {name}: {e}')
            return None
        finally:
            conn.close()

    if cached_val:
        val = cached_val['value']
        mode = cached_val.get('mode', 'single')

        if mode == 'single':
            return val

        elif mode == 'random':
            if isinstance(val, list) and val:
                return random.choice(val)
            return val

        elif mode == 'sequential':
            if isinstance(val, list) and val:
                with hub._lock:
                    idx = hub._sequential_counters.get(cache_key, 0)
                    if idx >= len(val): idx = 0
                    selected = val[idx]
                    hub._sequential_counters[cache_key] = (idx + 1) % len(val)
                return selected
            return val

    return None

########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\variable_manager_service\variable_manager_service\__init__.py total lines 317 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from flowork_kernel.services.base_service import BaseService
import importlib
import os
import logging
import asyncio
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


class VariableManagerService(BaseService):
    MAX_USER_CACHE_SIZE = 100
    SYSTEM_GLOBAL_KEYS = ['OPENAI_API_KEY', 'GEMINI_API_KEY', 'ANTHROPIC_API_KEY', 'FLOWORK_API_KEY', 'STABILITY_API_KEY', 'GROQ_API_KEY', 'DEEPSEEK_API_KEY']
    def _get_db_connection(self):
        db_service = getattr(self.kernel, 'database_service', None)
        if not db_service and hasattr(self.kernel, 'services'):
            db_service = self.kernel.services.get('database_service')
        if db_service:
            return db_service.create_connection()
        return None
    def autodiscover_and_sync_variables(self):
        """
            [REPAIR] Ensures all global keys appear in the UI.
            If not in Environment, creates a placeholder in DB.
            """
        for key in self.SYSTEM_GLOBAL_KEYS:
            env_val = os.environ.get(key)
            existing = self.get_variable_metadata(key, user_id=None)
            if not existing:
                if env_val:
                    self.kernel.write_to_log(f'[AutoSync] Injecting {key} from Environment to DB', 'INFO')
                    self.set_variable(key, env_val, is_secret=True, is_enabled=True, mode='single', user_id=None)
                else:
                    self.kernel.write_to_log(f'[AutoSync] Seeding UI placeholder for system key: {key}', 'DEBUG')
                    self.set_variable(key, 'PLEASE_EDIT_ME', is_secret=True, is_enabled=True, mode='single', user_id=None)
    def _get_user_variables_path(self, user_id: str):
        pass
    def _load_variables_from_file(self, user_id: str):
        pass
    def _save_variables_to_file(self, user_id: str, data_to_save: dict):
        pass
    def get_all_variables_for_api(self, user_id: str):
        conn = self._get_db_connection()
        if not conn:
            return []
        try:
            conn.row_factory = sqlite3.Row
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
                result.append({'name': row['name'], 'value': final_value, 'is_secret': is_secret, 'is_enabled': bool(row['is_enabled']), 'mode': row['mode'], 'is_protected': row['name'] in self.SYSTEM_GLOBAL_KEYS})
            return result
        except Exception as e:
            self.kernel.write_to_log(f'[VariableManager] Get All Error: {e}', 'ERROR')
            return []
        finally:
            conn.close()
    def get_variable_metadata(self, name, user_id: str=None):
        conn = self._get_db_connection()
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
            return {'name': target_data['name'], 'value': val_parsed, 'is_secret': bool(target_data['is_secret']), 'is_enabled': bool(target_data['is_enabled']), 'mode': target_data['mode'], 'is_protected': target_data['name'] in self.SYSTEM_GLOBAL_KEYS}
        except Exception as e:
            self.kernel.write_to_log(f'[VariableManager] Get Metadata Error for {name}: {e}', 'ERROR')
            return None
        finally:
            conn.close()
    def get_variable(self, name, user_id: str=None):
        cache_key = f'{user_id}_{name}'
        cached_val = None
        with self._lock:
            if cache_key in self._variables_data_cache:
                cached_val = self._variables_data_cache[cache_key]
        if cached_val is None:
            conn = self._get_db_connection()
            if not conn:
                return None
            try:
                conn.row_factory = sqlite3.Row
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
                with self._lock:
                    self._variables_data_cache[cache_key] = cached_val
            except Exception as e:
                self.kernel.write_to_log(f'[VariableManager] Error fetching {name}: {e}', 'ERROR')
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
                    selected = random.choice(val)
                    return selected
                return val
            elif mode == 'sequential':
                if isinstance(val, list) and val:
                    with self._lock:
                        idx = self._sequential_counters.get(cache_key, 0)
                        if idx >= len(val):
                            idx = 0
                        selected = val[idx]
                        self._sequential_counters[cache_key] = (idx + 1) % len(val)
                    return selected
                return val
        return None
    def set_variable(self, name, value, is_secret, is_enabled=True, mode='single', user_id: str=None):
        if name in self.SYSTEM_GLOBAL_KEYS:
            user_id = None
        conn = self._get_db_connection()
        if not conn:
            return False
        try:
            db_value = value
            is_already_encoded = False
            if is_secret and (db_value == '' or db_value is None):
                check_cursor = conn.cursor()
                if user_id:
                    check_cursor.execute('SELECT value FROM Variables WHERE user_id = ? AND name = ?', (user_id, name))
                else:
                    check_cursor.execute('SELECT value FROM Variables WHERE user_id IS NULL AND name = ?', (name,))
                existing_row = check_cursor.fetchone()
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
            cursor = conn.cursor()
            if name in self.SYSTEM_GLOBAL_KEYS:
                cursor.execute('DELETE FROM Variables WHERE user_id IS NULL AND name = ?', (name,))
            query = '\n            INSERT INTO Variables (user_id, name, value, is_secret, is_enabled, mode)\n            VALUES (?, ?, ?, ?, ?, ?)\n            ON CONFLICT(user_id, name) DO UPDATE SET\n                value=excluded.value,\n                is_secret=excluded.is_secret,\n                is_enabled=excluded.is_enabled,\n                mode=excluded.mode\n            '
            cursor.execute(query, (user_id, name, db_value, 1 if is_secret else 0, 1 if is_enabled else 0, mode))
            conn.commit()
            with self._lock:
                self._variables_data_cache.clear()
                self._sequential_counters.pop(f'{user_id}_{name}', None)
            return True
        except Exception as e:
            self.kernel.write_to_log(f'[VariableManager] Save Error: {e}', 'ERROR')
            return False
        finally:
            conn.close()
    def delete_variable(self, name, user_id: str):
        if name in self.SYSTEM_GLOBAL_KEYS:
            return False
        conn = self._get_db_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            if user_id:
                cursor.execute('DELETE FROM Variables WHERE user_id = ? AND name = ?', (user_id, name))
            else:
                cursor.execute('DELETE FROM Variables WHERE user_id IS NULL AND name = ?', (name,))
            conn.commit()
            with self._lock:
                self._variables_data_cache.clear()
            return True
        except:
            return False
        finally:
            conn.close()
    def set_variable_enabled_state(self, name, is_enabled, user_id: str=None):
        conn = self._get_db_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            val = 1 if is_enabled else 0
            target_uid = user_id
            if name in self.SYSTEM_GLOBAL_KEYS:
                target_uid = None
            if target_uid:
                cursor.execute('UPDATE Variables SET is_enabled = ? WHERE user_id = ? AND name = ?', (val, target_uid, name))
            else:
                cursor.execute('UPDATE Variables SET is_enabled = ? WHERE name = ?', (val, name))
            conn.commit()
            with self._lock:
                self._variables_data_cache.clear()
            return True
        except:
            return False
        finally:
            conn.close()

    def __init__(self, kernel, service_id: str):
        self.cells = {}
        if not hasattr(self, 'logger'):
            self.logger = logging.getLogger('LazyHub')
        super().__init__(kernel, service_id)
        self.users_data_path = os.path.normpath(os.path.join(self.kernel.data_path, 'users'))
        if not os.path.exists(self.users_data_path):
            try:
                os.makedirs(self.users_data_path, exist_ok=True)
            except Exception:
                pass
        self._variables_data_cache = OrderedDict()
        self._sequential_counters = {}
        self._lock = threading.Lock()
        self.autodiscover_and_sync_variables()
        self.kernel.write_to_log(f"Service 'VariableManager' ready. Storage Engine: SQLite (Flowork Core DB)", 'DEBUG')

    def execute_sync(self, cell_name, *args, **kwargs):
        module = self._load_cell(cell_name)
        return module.run(self, *args, **kwargs)

    async def execute_async(self, cell_name, *args, **kwargs):
        module = self._load_cell(cell_name)
        return await module.run(self, *args, **kwargs)

    def _load_cell(self, cell_name):
        if cell_name not in self.cells:
            try:
                module = importlib.import_module(f".{cell_name}", package=__package__)
                self.cells[cell_name] = module
                if hasattr(self, 'logger'):
                    self.logger.info(f"[LazyHub] ✅ Loaded: {cell_name}.py")
            except Exception as e:
                if hasattr(self, 'logger'):
                    self.logger.error(f"[LazyHub] ❌ Failed to load '{cell_name}': {e}")
                raise e
        return self.cells[cell_name]

    def start(self, *args, **kwargs):
        return self.execute_sync('start', *args, **kwargs)

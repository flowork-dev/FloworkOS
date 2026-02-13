########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\state_manager_service\state_manager_service\__init__.py total lines 132 
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
import shutil
import threading
from collections import OrderedDict


class StateManagerService(BaseService):
    GLOBAL_STATE_FILENAME = 'state.json'
    USER_STATE_FILENAME = 'state.json'
    MAX_USER_CACHE_SIZE = 100
    def _atomic_write(self, filepath, data):
        tmp_path = filepath + '.tmp'
        try:
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, filepath)
        except Exception as e:
            self.kernel.write_to_log(f'StateManager: ATOMIC WRITE FAILED: {e}', 'ERROR')
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    def _load_global_state(self):
        try:
            if os.path.exists(self.global_state_file_path):
                with open(self.global_state_file_path, 'r', encoding='utf-8') as f:
                    self._global_state_cache = json.load(f)
            else:
                self._global_state_cache = {}
        except:
            self._global_state_cache = {}
    def _save_global_state(self):
        self._atomic_write(self.global_state_file_path, self._global_state_cache)
    def _get_user_state_path(self, user_id: str):
        user_dir = os.path.join(self.users_data_path, user_id)
        os.makedirs(user_dir, exist_ok=True)
        return os.path.join(user_dir, self.USER_STATE_FILENAME)
    def _load_user_state_from_file(self, user_id: str):
        state_file_path = self._get_user_state_path(user_id)
        try:
            if os.path.exists(state_file_path):
                with open(state_file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except:
            return {}
    def _save_user_state_to_file(self, user_id: str, state_data: dict):
        state_file_path = self._get_user_state_path(user_id)
        self._atomic_write(state_file_path, state_data)
    def get(self, key, user_id: str=None, default=None):
        with self._lock:
            if user_id:
                if user_id not in self._user_state_cache:
                    self._user_state_cache[user_id] = self._load_user_state_from_file(user_id)
                return self._user_state_cache[user_id].get(key, default)
            return self._global_state_cache.get(key, default)
    def set(self, key, value, user_id: str=None):
        with self._lock:
            if user_id:
                if user_id not in self._user_state_cache:
                    self._user_state_cache[user_id] = self._load_user_state_from_file(user_id)
                self._user_state_cache[user_id][key] = value
                self._save_user_state_to_file(user_id, self._user_state_cache[user_id])
            else:
                self._global_state_cache[key] = value
                self._save_global_state()
    async def handle_get_active_apps(self, request):
        user_id = request.headers.get('X-Flowork-User-ID', 'default')
        active = self.get('active_apps', user_id=user_id, default=[])
        return {'status': 'success', 'active_apps': active}
    async def handle_save_active_apps(self, request):
        user_id = request.headers.get('X-Flowork-User-ID', 'default')
        data = request.json
        active_apps = data if isinstance(data, list) else data.get('active_apps', [])
        self.set('active_apps', active_apps, user_id=user_id)
        return {'status': 'success', 'message': 'Active apps list saved.'}
    def update_all(self, data: dict, user_id: str=None):
        pass
    def delete(self, key, user_id: str=None):
        pass
    def get_all(self, user_id: str=None):
        return {}

    def __init__(self, kernel, service_id: str):
        self.cells = {}
        if not hasattr(self, 'logger'):
            self.logger = logging.getLogger('LazyHub')
        super().__init__(kernel, service_id)
        self.users_data_path = os.path.join(self.kernel.data_path, 'users')
        self.global_state_file_path = os.path.join(self.kernel.data_path, self.GLOBAL_STATE_FILENAME)
        os.makedirs(self.users_data_path, exist_ok=True)
        self._global_state_cache = {}
        self._user_state_cache = OrderedDict()
        self._lock = threading.Lock()
        self.kernel.write_to_log("Service 'StateManager' (Hybrid Multi-Tenant) initialized.", 'DEBUG')
        self._load_global_state()

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

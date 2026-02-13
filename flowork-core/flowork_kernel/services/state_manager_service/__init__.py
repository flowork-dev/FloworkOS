########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\state_manager_service\__init__.py total lines 85 
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

    def _atomic_write(self, *args, **kwargs):
        return self.execute_sync('_atomic_write', *args, **kwargs)
    def _load_global_state(self, *args, **kwargs):
        return self.execute_sync('_load_global_state', *args, **kwargs)
    def _save_global_state(self, *args, **kwargs):
        return self.execute_sync('_save_global_state', *args, **kwargs)
    def _get_user_state_path(self, *args, **kwargs):
        return self.execute_sync('_get_user_state_path', *args, **kwargs)
    def _load_user_state_from_file(self, *args, **kwargs):
        return self.execute_sync('_load_user_state_from_file', *args, **kwargs)
    def _save_user_state_to_file(self, *args, **kwargs):
        return self.execute_sync('_save_user_state_to_file', *args, **kwargs)
    def get(self, *args, **kwargs):
        return self.execute_sync('get', *args, **kwargs)
    def set(self, *args, **kwargs):
        return self.execute_sync('set', *args, **kwargs)
    async def handle_get_active_apps(self, *args, **kwargs):
        return await self.execute_async('handle_get_active_apps', *args, **kwargs)
    async def handle_save_active_apps(self, *args, **kwargs):
        return await self.execute_async('handle_save_active_apps', *args, **kwargs)
    def update_all(self, *args, **kwargs):
        return self.execute_sync('update_all', *args, **kwargs)
    def delete(self, *args, **kwargs):
        return self.execute_sync('delete', *args, **kwargs)
    def get_all(self, *args, **kwargs):
        return self.execute_sync('get_all', *args, **kwargs)

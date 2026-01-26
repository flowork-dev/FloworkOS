########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\preset_manager_service\__init__.py total lines 86 
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
import datetime
import threading
from flowork_kernel.exceptions import PresetNotFoundError
from flowork_kernel.utils.flowchain_verifier import verify_workflow_chain, calculate_hash
from flowork_kernel.services.database_service.database_service import DatabaseService
from flowork_kernel.singleton import Singleton
import logging


class PresetManagerService(BaseService):
    def __init__(self, kernel, service_id: str):
        self.cells = {}
        if not hasattr(self, 'logger'):
            self.logger = logging.getLogger('LazyHub')
        super().__init__(kernel, service_id)
        possible_paths = ['/app/data/users', 'C:\\FLOWORK\\data\\users', os.path.join(self.kernel.data_path, 'users')]
        self.users_data_path = next((p for p in possible_paths if os.path.exists(os.path.dirname(p))), possible_paths[1])
        os.makedirs(self.users_data_path, exist_ok=True)
        self._save_lock = threading.Lock()
        self.state_manager = self.kernel.get_service('state_manager_service')
        self.trigger_manager = None
        self.db_service = None
        self.logger.info(f'Preset Manager Storage: {self.users_data_path}')

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
    def _get_workflow_id(self, *args, **kwargs):
        return self.execute_sync('_get_workflow_id', *args, **kwargs)
    def _get_user_presets_path(self, *args, **kwargs):
        return self.execute_sync('_get_user_presets_path', *args, **kwargs)
    def _get_preset_workflow_path(self, *args, **kwargs):
        return self.execute_sync('_get_preset_workflow_path', *args, **kwargs)
    def _get_latest_version_file(self, *args, **kwargs):
        return self.execute_sync('_get_latest_version_file', *args, **kwargs)
    def _sync_trigger_rules_for_preset(self, *args, **kwargs):
        return self.execute_sync('_sync_trigger_rules_for_preset', *args, **kwargs)
    def get_preset_list(self, *args, **kwargs):
        return self.execute_sync('get_preset_list', *args, **kwargs)
    def get_preset_data(self, *args, **kwargs):
        return self.execute_sync('get_preset_data', *args, **kwargs)
    def save_preset(self, *args, **kwargs):
        return self.execute_sync('save_preset', *args, **kwargs)
    def delete_preset(self, *args, **kwargs):
        return self.execute_sync('delete_preset', *args, **kwargs)
    def get_preset_versions(self, *args, **kwargs):
        return self.execute_sync('get_preset_versions', *args, **kwargs)
    def load_preset_version(self, *args, **kwargs):
        return self.execute_sync('load_preset_version', *args, **kwargs)
    def delete_preset_version(self, *args, **kwargs):
        return self.execute_sync('delete_preset_version', *args, **kwargs)

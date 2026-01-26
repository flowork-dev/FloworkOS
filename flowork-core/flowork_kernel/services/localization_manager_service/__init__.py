########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\localization_manager_service\__init__.py total lines 84 
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
from collections import OrderedDict


class LocalizationManagerService(BaseService):
    SETTINGS_FILE = 'settings.json'
    MAX_USER_SETTINGS_CACHE = 50

    def __init__(self, kernel, service_id: str):
        self.cells = {}
        if not hasattr(self, 'logger'):
            self.logger = logging.getLogger('LazyHub')
        super().__init__(kernel, service_id)
        self.locales_path = self.kernel.locales_path
        self.users_data_path = os.path.join(self.kernel.data_path, 'users')
        self.languages = {}
        self.current_lang = 'en'
        self._settings_cache = OrderedDict()
        self.language_map = {'en': 'English', 'id': 'Bahasa Indonesia'}
        os.makedirs(self.locales_path, exist_ok=True)
        os.makedirs(self.users_data_path, exist_ok=True)
        self.kernel.write_to_log("Service 'LocalizationManager' (Multi-Tenant) initialized.", 'DEBUG')
        self.load_base_languages()

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

    def get_available_languages_display(self, *args, **kwargs):
        return self.execute_sync('get_available_languages_display', *args, **kwargs)
    def get_current_language_code(self, *args, **kwargs):
        return self.execute_sync('get_current_language_code', *args, **kwargs)
    def load_base_languages(self, *args, **kwargs):
        return self.execute_sync('load_base_languages', *args, **kwargs)
    def load_all_languages(self, *args, **kwargs):
        return self.execute_sync('load_all_languages', *args, **kwargs)
    def _merge_from_directory(self, *args, **kwargs):
        return self.execute_sync('_merge_from_directory', *args, **kwargs)
    def set_language(self, *args, **kwargs):
        return self.execute_sync('set_language', *args, **kwargs)
    def get(self, *args, **kwargs):
        return self.execute_sync('get', *args, **kwargs)
    def _get_user_settings_path(self, *args, **kwargs):
        return self.execute_sync('_get_user_settings_path', *args, **kwargs)
    def _load_settings_from_file(self, *args, **kwargs):
        return self.execute_sync('_load_settings_from_file', *args, **kwargs)
    def _save_settings(self, *args, **kwargs):
        return self.execute_sync('_save_settings', *args, **kwargs)
    def save_setting(self, *args, **kwargs):
        return self.execute_sync('save_setting', *args, **kwargs)
    def get_setting(self, *args, **kwargs):
        return self.execute_sync('get_setting', *args, **kwargs)
    def get_all_settings(self, *args, **kwargs):
        return self.execute_sync('get_all_settings', *args, **kwargs)

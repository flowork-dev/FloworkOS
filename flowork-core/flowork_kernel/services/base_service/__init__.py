########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\base_service\__init__.py total lines 85 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import importlib
import os
import logging
import asyncio
import logging
import os
import shutil
import time
import traceback
import threading
from enum import Enum
from pathlib import Path

class RecoveryTier(Enum):
    TIER_1_SELF_HEAL = 1
    TIER_2_SOFT_RESTART = 2
    TIER_3_HARD_RESTART = 3
    TIER_4_KERNEL_PANIC = 4

class BaseService():
    def __init__(self, kernel, service_id: str, vitality_doctor=None):
        self.cells = {}
        if not hasattr(self, 'logger'):
            self.logger = logging.getLogger('LazyHub')
        self.kernel = kernel
        self.service_id = service_id
        self.doctor = vitality_doctor
        self.logger = logging.getLogger(f'Node.{service_id}')
        self._loc_cache = None
        self.is_running = False
        self.retry_count = 0
        self.max_retries = 3

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

    def _resolve_and_secure_path(self, *args, **kwargs):
        return self.execute_sync('_resolve_and_secure_path', *args, **kwargs)
    def secure_list_directory(self, *args, **kwargs):
        return self.execute_sync('secure_list_directory', *args, **kwargs)
    def secure_create_folder(self, *args, **kwargs):
        return self.execute_sync('secure_create_folder', *args, **kwargs)
    def secure_delete_path(self, *args, **kwargs):
        return self.execute_sync('secure_delete_path', *args, **kwargs)
    def run_logic(self, *args, **kwargs):
        return self.execute_sync('run_logic', *args, **kwargs)
    def start(self, *args, **kwargs):
        return self.execute_sync('start', *args, **kwargs)
    def _immortal_loop(self, *args, **kwargs):
        return self.execute_sync('_immortal_loop', *args, **kwargs)
    def handle_injury(self, *args, **kwargs):
        return self.execute_sync('handle_injury', *args, **kwargs)
    def stop(self, *args, **kwargs):
        return self.execute_sync('stop', *args, **kwargs)
    def cleanup_resources(self, *args, **kwargs):
        return self.execute_sync('cleanup_resources', *args, **kwargs)

    @property
    def loc(self):
        """Shortcut to Localization Manager"""
        return self.kernel.get_service("localization_manager")

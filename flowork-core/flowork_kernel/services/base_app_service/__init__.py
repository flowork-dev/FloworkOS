########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\base_app_service\__init__.py total lines 56 
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
import shutil
from pathlib import Path


class BaseAppService(BaseService):
    def __init__(self, *args, **kwargs):
        self.cells = {}
        if not hasattr(self, 'logger'): self.logger = logging.getLogger("LazyHub")
        super().__init__(*args, **kwargs)

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

    def get_library_warehouse_path(self):
        """Kembalikan alamat gudang library global"""
        return os.path.join(self.kernel.data_path, "global_libs")

    def _to_virtual_path(self, *args, **kwargs):
        return self.execute_sync('_to_virtual_path', *args, **kwargs)
    def _resolve_and_secure_path(self, *args, **kwargs):
        return self.execute_sync('_resolve_and_secure_path', *args, **kwargs)
    def secure_list_directory(self, *args, **kwargs):
        return self.execute_sync('secure_list_directory', *args, **kwargs)
    def secure_create_folder(self, *args, **kwargs):
        return self.execute_sync('secure_create_folder', *args, **kwargs)
    def secure_delete_path(self, *args, **kwargs):
        return self.execute_sync('secure_delete_path', *args, **kwargs)

########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\library_manager_service\__init__.py total lines 76 
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
import sys
import subprocess
import hashlib
import json
import threading
from concurrent.futures import ThreadPoolExecutor


class LibraryManagerService(BaseService):
    def __init__(self, kernel, service_id: str):
        self.cells = {}
        if not hasattr(self, 'logger'):
            self.logger = logging.getLogger('LazyHub.Warehouse')

        super().__init__(kernel, service_id)

        self.warehouse_path = os.path.join(self.kernel.project_root_path, 'data', 'global_libs')
        if not os.path.exists(self.warehouse_path):
            os.makedirs(self.warehouse_path)

        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix='LibInstaller')
        self.logger.info(f'📚 [LibraryManager] Warehouse initialized at: {self.warehouse_path}')

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
                self.logger.info(f"[LazyHub] ✅ Loaded: {cell_name}.py")
            except Exception as e:
                self.logger.error(f"[LazyHub] ❌ Failed to load '{cell_name}': {e}")
                raise e
        return self.cells[cell_name]

    def _install_package(self, requirement, target_dir):
        """Menjalankan pip install --target ke alamat gudang [cite: 16]"""
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install",
                requirement, "--target", target_dir, "--no-cache-dir"
            ])
            return True
        except Exception as e:
            self.logger.error(f"❌ [Pip] Install error for {requirement}: {e}")
            return False

    def resolve_dependencies(self, *args, **kwargs):
        return self.execute_sync('resolve_dependencies', *args, **kwargs)

    def get_injection_paths(self, *args, **kwargs):
        return self.execute_sync('get_injection_paths', *args, **kwargs)

    def start(self, *args, **kwargs):
        return self.execute_sync('start', *args, **kwargs)

    def stop(self, *args, **kwargs):
        return self.execute_sync('stop', *args, **kwargs)

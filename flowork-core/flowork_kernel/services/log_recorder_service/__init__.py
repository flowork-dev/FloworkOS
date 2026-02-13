########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\log_recorder_service\__init__.py total lines 67 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import importlib
import os
import logging
import asyncio
import os
import json
import time
import logging
from logging.handlers import RotatingFileHandler
from flowork_kernel.services.base_service import BaseService


class LogRecorderService(BaseService):
    def __init__(self, kernel, service_id):
        self.cells = {}
        if not hasattr(self, 'logger'):
            self.logger = logging.getLogger('LazyHub')
        super().__init__(kernel, service_id)
        self.log_dir = os.path.join(self.kernel.project_root_path, 'data', 'logs')
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir, exist_ok=True)
        self.file_logger = logging.getLogger('FloworkBlackbox')
        self.file_logger.setLevel(logging.INFO)
        self.file_logger.propagate = False
        log_file_path = os.path.join(self.log_dir, 'flowork_system.log')
        handler = RotatingFileHandler(log_file_path, maxBytes=10 * 1024 * 1024, backupCount=5, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] [%(name)s] %(message)s')
        handler.setFormatter(formatter)
        self.file_logger.addHandler(handler)

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
    def stop(self, *args, **kwargs):
        return self.execute_sync('stop', *args, **kwargs)
    def _record_system_log(self, *args, **kwargs):
        return self.execute_sync('_record_system_log', *args, **kwargs)
    def _record_app_log(self, *args, **kwargs):
        return self.execute_sync('_record_app_log', *args, **kwargs)
    def _record_app_error(self, *args, **kwargs):
        return self.execute_sync('_record_app_error', *args, **kwargs)

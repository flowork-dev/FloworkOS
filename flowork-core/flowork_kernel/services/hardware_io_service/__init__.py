########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\hardware_io_service\__init__.py total lines 55 
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
import sys
import logging
from flowork_kernel.services.base_service import BaseService


class HardwareIOService(BaseService):
    def __init__(self, kernel, service_id):
        self.cells = {}
        if not hasattr(self, 'logger'):
            self.logger = logging.getLogger('LazyHub')
        super().__init__(kernel, service_id)
        self.available_sensors = []
        self.audio_devices = []
        self.is_hardware_isolated = True

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
    def _scan_hardware_capabilities(self, *args, **kwargs):
        return self.execute_sync('_scan_hardware_capabilities', *args, **kwargs)
    def capture_audio_sample(self, *args, **kwargs):
        return self.execute_sync('capture_audio_sample', *args, **kwargs)
    def stop(self, *args, **kwargs):
        return self.execute_sync('stop', *args, **kwargs)

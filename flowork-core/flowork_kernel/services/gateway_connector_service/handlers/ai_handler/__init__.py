########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\gateway_connector_service\handlers\ai_handler\__init__.py total lines 51 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import importlib
import os
import logging
import asyncio
import json
from flowork_kernel.singleton import Singleton

from flowork_kernel.services.gateway_connector_service.handlers.base_handler import BaseHandler, CURRENT_PAYLOAD_VERSION

class AIHandler(BaseHandler):
    def __init__(self, *args, **kwargs):
        self.cells = {}
        if not hasattr(self, 'logger'):
            self.logger = logging.getLogger("LazyHub")
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

    def _get_app_instance(self, *args, **kwargs):
        return self.execute_sync('_get_app_instance', *args, **kwargs)

    def _send_training_status(self, *args, **kwargs):
        return self.execute_sync('_send_training_status', *args, **kwargs)

    def register_events(self, *args, **kwargs):
        return self.execute_sync('register_events', *args, **kwargs)

########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\engine_routes\__init__.py total lines 61 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from flowork_kernel.services.api_server_service.routes.base_api_route import BaseApiRoute
import importlib
import os
import logging
import asyncio
import datetime
import time
import json
from flowork_kernel.exceptions import PermissionDeniedError
from collections import Counter, defaultdict
from flowork_kernel.singleton import Singleton
from flowork_kernel.services.database_service.database_service import DatabaseService


class EngineRoutes(BaseApiRoute):
    def __init__(self, service_instance):
        self.cells = {}
        if not hasattr(self, 'logger'):
            self.logger = logging.getLogger('LazyHub')
        super().__init__(service_instance)
        self._boot_time = datetime.datetime.utcnow()

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

    def os_scheduler(self, *args, **kwargs):
        return self.execute_sync('os_scheduler', *args, **kwargs)
    def register_routes(self, *args, **kwargs):
        return self.execute_sync('register_routes', *args, **kwargs)
    async def handle_get_live_stats(self, *args, **kwargs):
        return await self.execute_async('handle_get_live_stats', *args, **kwargs)
    def _build_empty_stats(self, *args, **kwargs):
        return self.execute_sync('_build_empty_stats', *args, **kwargs)
    async def handle_schedule_action(self, *args, **kwargs):
        return await self.execute_async('handle_schedule_action', *args, **kwargs)
    async def handle_cancel_schedule(self, *args, **kwargs):
        return await self.execute_async('handle_cancel_schedule', *args, **kwargs)

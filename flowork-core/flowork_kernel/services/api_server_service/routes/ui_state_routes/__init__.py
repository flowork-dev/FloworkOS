########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\ui_state_routes\__init__.py total lines 59 
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
import threading


class UIStateRoutes(BaseApiRoute):
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

    def register_routes(self, *args, **kwargs):
        return self.execute_sync('register_routes', *args, **kwargs)
    async def get_dashboard_state(self, *args, **kwargs):
        return await self.execute_async('get_dashboard_state', *args, **kwargs)
    async def set_dashboard_state(self, *args, **kwargs):
        return await self.execute_async('set_dashboard_state', *args, **kwargs)
    async def get_session_tabs(self, *args, **kwargs):
        return await self.execute_async('get_session_tabs', *args, **kwargs)
    async def set_session_tabs(self, *args, **kwargs):
        return await self.execute_async('set_session_tabs', *args, **kwargs)
    async def get_generic_state(self, *args, **kwargs):
        return await self.execute_async('get_generic_state', *args, **kwargs)
    async def set_generic_state(self, *args, **kwargs):
        return await self.execute_async('set_generic_state', *args, **kwargs)
    def _update_permissions_synchronous(self, *args, **kwargs):
        return self.execute_sync('_update_permissions_synchronous', *args, **kwargs)
    async def delete_generic_state(self, *args, **kwargs):
        return await self.execute_async('delete_generic_state', *args, **kwargs)

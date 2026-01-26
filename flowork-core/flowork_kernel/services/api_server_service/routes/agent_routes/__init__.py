########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\agent_routes\__init__.py total lines 67 
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
from aiohttp import web
import json
import asyncio


class AgentRoutes(BaseApiRoute):
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
    async def handle_chat_completions(self, *args, **kwargs):
        return await self.execute_async('handle_chat_completions', *args, **kwargs)
    async def _stream_council_session(self, *args, **kwargs):
        return await self.execute_async('_stream_council_session', *args, **kwargs)
    async def _stream_standard_chat(self, *args, **kwargs):
        return await self.execute_async('_stream_standard_chat', *args, **kwargs)
    async def handle_get_agents(self, *args, **kwargs):
        return await self.execute_async('handle_get_agents', *args, **kwargs)
    async def handle_get_agent(self, *args, **kwargs):
        return await self.execute_async('handle_get_agent', *args, **kwargs)
    async def handle_post_agents(self, *args, **kwargs):
        return await self.execute_async('handle_post_agents', *args, **kwargs)
    async def handle_delete_agent(self, *args, **kwargs):
        return await self.execute_async('handle_delete_agent', *args, **kwargs)
    async def handle_run_agent(self, *args, **kwargs):
        return await self.execute_async('handle_run_agent', *args, **kwargs)
    async def handle_get_agent_run_status(self, *args, **kwargs):
        return await self.execute_async('handle_get_agent_run_status', *args, **kwargs)
    async def handle_stop_agent_run(self, *args, **kwargs):
        return await self.execute_async('handle_stop_agent_run', *args, **kwargs)
    async def handle_run_agent_task_adhoc(self, *args, **kwargs):
        return await self.execute_async('handle_run_agent_task_adhoc', *args, **kwargs)

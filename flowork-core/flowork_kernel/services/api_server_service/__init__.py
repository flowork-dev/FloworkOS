########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\__init__.py total lines 104 
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
import inspect
from aiohttp import web

class ApiServerService(BaseService):
    def __init__(self, kernel, service_id: str):
        self.cells = {}
        if not hasattr(self, 'logger'):
            self.logger = logging.getLogger('LazyHub.API')

        super().__init__(kernel, service_id)
        self.app = None
        self.runner = None
        self.site = None
        self.routes = []

        self._discover_cells()

    def _discover_cells(self):
        package_path = os.path.dirname(__file__)
        if not os.path.exists(package_path): return
        for file in os.listdir(package_path):
            if file.endswith(".py") and not file.startswith("__"):
                cell_name = file[:-3]
                if not hasattr(self, cell_name):
                    setattr(self, cell_name, self._make_dynamic_handler(cell_name))

    def _make_dynamic_handler(self, cell_name):
        async def handler(*args, **kwargs):
            return await self.execute(cell_name, *args, **kwargs)
        return handler

    async def execute(self, cell_name, *args, **kwargs):
        module = self._load_cell(cell_name)
        if not module: return None
        if inspect.iscoroutinefunction(module.run):
            res = await module.run(self, *args, **kwargs)
        else:
            res = module.run(self, *args, **kwargs)
        if inspect.isawaitable(res): return await res
        return res

    def execute_sync(self, cell_name, *args, **kwargs):
        module = self._load_cell(cell_name)
        if not module: return None
        if inspect.iscoroutinefunction(module.run):
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running(): return module.run(self, *args, **kwargs)
                return loop.run_until_complete(module.run(self, *args, **kwargs))
            except: return asyncio.run(module.run(self, *args, **kwargs))
        return module.run(self, *args, **kwargs)

    async def execute_async(self, cell_name, *args, **kwargs):
        return await self.execute(cell_name, *args, **kwargs)

    def _load_cell(self, cell_name):
        if cell_name == 'logger': return None
        if cell_name not in self.cells:
            try:
                module = importlib.import_module(f".{cell_name}", package=__package__)
                self.cells[cell_name] = module
                self.logger.info(f"[LazyHub] ✅ Loaded: {cell_name}.py")
            except Exception as e:
                self.logger.error(f"[LazyHub] ❌ Failed to load '{cell_name}': {e}")
                raise e
        return self.cells[cell_name]

    async def dynamic_service_gateway(self, request):
        service_name = request.match_info.get('service_name')
        action = request.match_info.get('action')
        try:
            payload = await request.json()
        except:
            payload = {}

        self.logger.info(f"📡 [UniversalGateway] Proxying request to {service_name}->{action}")

        muscle = self.kernel.get_service("app_runtime")
        if not muscle:
            return web.json_response({"error": "AppRuntime Service Offline"}, status=503)

        result = await muscle.execute_service_action(
            app_id=service_name,
            action_name=action,
            data=payload
        )
        return web.json_response(result)

    async def start(self, *args, **kwargs): return await self.execute('start', *args, **kwargs)
    async def stop(self, *args, **kwargs): return await self.execute('stop', *args, **kwargs)
    def _load_api_routes(self, *args, **kwargs): return self.execute_sync('_load_api_routes', *args, **kwargs)
    async def handle_app_execute(self, request): return await self.execute('handle_app_execute', request)
    async def handle_ai_query(self, request): return await self.execute('handle_ai_query', request)

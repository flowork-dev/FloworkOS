########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\app_runtime_service\__init__.py total lines 76 
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

class AppRuntimeService(BaseService):
    def __init__(self, kernel, service_id: str):
        self.cells = {}
        if not hasattr(self, 'logger'):
            self.logger = logging.getLogger('LazyHub.Muscle')
        super().__init__(kernel, service_id)
        self._discover_cells()

    def _discover_cells(self):
        package_path = os.path.dirname(__file__)
        if not os.path.exists(package_path): return
        for file in os.listdir(package_path):
            if file.endswith(".py") and not file.startswith("__"):
                cell_name = file[:-3]
                if not hasattr(self, cell_name):
                    setattr(self, cell_name, self._make_executor(cell_name))

    def _make_executor(self, cell_name):
        async def handler(*args, **kwargs):
            return await self.execute(cell_name, *args, **kwargs)
        return handler

    async def execute(self, cell_name, *args, **kwargs):
        module = self._load_cell(cell_name)
        if not module: return None
        res = module.run(self, *args, **kwargs)
        if inspect.isawaitable(res): return await res
        return res

    def execute_sync(self, cell_name, *args, **kwargs):
        module = self._load_cell(cell_name)
        if not module: return None
        if inspect.iscoroutinefunction(module.run):
            loop = asyncio.get_event_loop()
            if loop.is_running(): return module.run(self, *args, **kwargs)
            return loop.run_until_complete(module.run(self, *args, **kwargs))
        return module.run(self, *args, **kwargs)

    def _load_cell(self, cell_name):
        if cell_name not in self.cells:
            try:
                module = importlib.import_module(f".{cell_name}", package=__package__)
                self.cells[cell_name] = module
                self.logger.info(f"[LazyHub] ✅ Muscle Loaded: {cell_name}.py")
            except Exception as e:
                self.logger.error(f"[LazyHub] ❌ Muscle Failed: {cell_name} -> {e}")
                raise e
        return self.cells[cell_name]

    async def execute_service_action(self, app_id: str, action_name: str, data: dict):
        """
        Menghubungi Runner App via Socket untuk eksekusi aksi.
        """
        return await self.execute('execute_service_action', app_id, action_name, data)

    async def start(self, *args, **kwargs): return await self.execute('start', *args, **kwargs)
    async def execute_app(self, *args, **kwargs): return await self.execute('execute_app', *args, **kwargs)

    async def create_atomic_cell(self, app_id: str, cell_name: str, code: str):
        """
        Menulis file .py baru ke dalam folder logic aplikasi target.
        """
        return await self.execute('create_atomic_cell', app_id, cell_name, code)

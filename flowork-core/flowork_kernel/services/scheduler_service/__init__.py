########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\scheduler_service\__init__.py total lines 56 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import importlib
import logging
import inspect
from flowork_kernel.services.base_service import BaseService

class SchedulerService(BaseService):
    def __init__(self, kernel, service_id: str = "scheduler_service"):
        super().__init__(kernel, service_id)
        self.logger = logging.getLogger("SchedulerService")
        self._cells_cache = {}
        self.active_schedules = []
        self.is_running = False


    async def execute(self, cell_name, *args, **kwargs):
        """
        DCD & Lazy Loading Engine.
        Signature: async def execute(self, cell_name, *args, **kwargs)
        """
        if cell_name not in self._cells_cache:
            try:
                module_path = f"flowork_kernel.services.scheduler_service.{cell_name}"
                module = importlib.import_module(module_path)
                importlib.reload(module)
                self._cells_cache[cell_name] = module
                self.logger.info(f"[LazyHub] ✅ Loaded: {cell_name}.py")
            except Exception as e:
                self.logger.error(f"❌ [Scheduler] Failed to load cell '{cell_name}': {e}")
                return None

        cell = self._cells_cache[cell_name]

        if inspect.iscoroutinefunction(cell.run):
            return await cell.run(self, *args, **kwargs)
        else:
            return cell.run(self, *args, **kwargs)

    def execute_sync(self, cell_name, *args, **kwargs):
        """Bridge for internal kernel sync calls."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return self.execute(cell_name, *args, **kwargs)
            return loop.run_until_complete(self.execute(cell_name, *args, **kwargs))
        except:
            return None

    async def start(self, *args, **kwargs): return await self.execute('start', *args, **kwargs)

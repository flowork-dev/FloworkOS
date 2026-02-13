########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\event_bus_service\__init__.py total lines 93 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import importlib
import os
import logging
import asyncio
import threading
import multiprocessing
import queue
from flowork_kernel.services.base_service import BaseService

class EventBusService(BaseService):
    def __init__(self, kernel, service_id, ipc_queue: multiprocessing.Queue = None):
        self.cells = {}
        if not hasattr(self, 'logger'):
            self.logger = logging.getLogger('LazyHub')

        super().__init__(kernel, service_id)

        self.subscribers = {}
        self.app_subscriptions = {}
        self.ipc_queue = ipc_queue
        self._app_runtime_cache = None
        self.is_main_bus = False
        self._main_loop = None
        self._ipc_thread = None
        self._stop_event = threading.Event()
        self.pub_max_retries = 3
        self.pub_backoff = 0.1
        self.ipc_thread_health = True

        if self.ipc_queue:
            self.logger.info(f"✅ EventBus initialized with IPC Queue (Neural Link Active).")
        else:
            self.logger.warning(f"⚠️ EventBus initialized WITHOUT IPC Queue. Cross-process bridging will FAIL.")

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

    def set_main_loop(self, *args, **kwargs):
        return self.execute_sync('set_main_loop', *args, **kwargs)

    def _start_ipc_listener(self, *args, **kwargs):
        return self.execute_sync('_start_ipc_listener', *args, **kwargs)

    def subscribe(self, *args, **kwargs):
        return self.execute_sync('subscribe', *args, **kwargs)

    def subscribe_app(self, *args, **kwargs):
        return self.execute_sync('subscribe_app', *args, **kwargs)

    def unsubscribe(self, *args, **kwargs):
        return self.execute_sync('unsubscribe', *args, **kwargs)

    def publish(self, *args, **kwargs):
        return self.execute_sync('publish', *args, **kwargs)

    def _dispatch_to_apps(self, *args, **kwargs):
        return self.execute_sync('_dispatch_to_apps', *args, **kwargs)

    def _dispatch_event(self, *args, **kwargs):
        return self.execute_sync('_dispatch_event', *args, **kwargs)

    def _run_ipc_listener_thread(self, *args, **kwargs):
        return self.execute_sync('_run_ipc_listener_thread', *args, **kwargs)

    async def load_dependencies(self, *args, **kwargs):
        return await self.execute_async('load_dependencies', *args, **kwargs)

    def run_logic(self, *args, **kwargs):
        return self.execute_sync('start', *args, **kwargs)

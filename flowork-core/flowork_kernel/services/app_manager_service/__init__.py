########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\app_manager_service\__init__.py total lines 100 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from flowork_kernel.services.base_service import BaseService
import importlib
import os
import logging
from flowork_kernel.utils.path_helper import get_apps_directory

class AppService(BaseService):
    def __init__(self, kernel, service_id: str):
        self.cells = {}
        if not hasattr(self, 'logger'):
            self.logger = logging.getLogger('LazyHub')
        super().__init__(kernel, service_id)

        self.base_app_path = os.environ.get('FLOWORK_APPS_DIR', str(get_apps_directory()))
        self.registry = {'apps': {'path': self.base_app_path, 'data': {}}}
        self.instances = {}
        self.port_registry = {}
        self.process_registry = {}
        self.next_port = 5001

        self.app_activity = {}
        self.last_activity = {} # Tambahan: Mencegah AttributeError pada GhostKeeper/Reaper

        self.ghost_timeout = 300
        self.is_ghost_active = True
        self.crash_tracker = {}
        self.quarantine_registry = {}
        self.CRASH_WINDOW = 60
        self.MAX_RESTARTS = 3

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


    def _ghost_reaper_loop(self, *args, **kwargs):
        return self.execute_sync('_ghost_reaper_loop', *args, **kwargs)

    def _setup_neural_listener(self, *args, **kwargs):
        return self.execute_sync('_setup_neural_listener', *args, **kwargs)

    def start(self, *args, **kwargs):
        return self.execute_sync('start', *args, **kwargs)

    def ensure_app_running(self, *args, **kwargs):
        return self.execute_sync('ensure_app_running', *args, **kwargs)

    def get_instance(self, *args, **kwargs):
        return self.execute_sync('get_instance', *args, **kwargs)

    def _touch_app_activity(self, *args, **kwargs):
        return self.execute_sync('_touch_app_activity', *args, **kwargs)

    def _check_immune_system(self, *args, **kwargs):
        return self.execute_sync('_check_immune_system', *args, **kwargs)

    def _perform_autoheal(self, *args, **kwargs):
        return self.execute_sync('_perform_autoheal', *args, **kwargs)

    def get_assigned_port(self, *args, **kwargs):
        return self.execute_sync('get_assigned_port', *args, **kwargs)

    def kill_app(self, *args, **kwargs):
        return self.execute_sync('kill_app', *args, **kwargs)

    def sync(self, *args, **kwargs):
        return self.execute_sync('sync', *args, **kwargs)

    def get_registry(self, *args, **kwargs):
        return self.execute_sync('get_registry', *args, **kwargs)

    def _bind_router_to_instance(self, *args, **kwargs):
        return self.execute_sync('_bind_router_to_instance', *args, **kwargs)

    def scaffold_app(self, app_name, *args, **kwargs):
        """Memicu pembuatan struktur folder aplikasi baru (Atomic Scaffolding)"""
        return self.execute_sync('scaffold_app', app_name, *args, **kwargs)

########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\node_manager_service\__init__.py total lines 69 
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
import json
import importlib.util
import sys
import logging
import inspect
from flowork_kernel.services.base_service import BaseService
from flowork_kernel.utils.path_helper import get_apps_directory


class NodeManagerService(BaseService):
    def __init__(self, kernel, service_id):
        self.cells = {}
        if not hasattr(self, 'logger'):
            self.logger = logging.getLogger('LazyHub')
        super().__init__(kernel, service_id)
        self.nodes_map = {}
        self.nodes_metadata = []
        self.base_apps_path = os.environ.get('FLOWORK_APPS_DIR', str(get_apps_directory()))

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
    def scan_nodes(self, *args, **kwargs):
        return self.execute_sync('scan_nodes', *args, **kwargs)
    def _process_manifest(self, *args, **kwargs):
        return self.execute_sync('_process_manifest', *args, **kwargs)
    def _load_single_node(self, *args, **kwargs):
        return self.execute_sync('_load_single_node', *args, **kwargs)
    def _register_node_class(self, *args, **kwargs):
        return self.execute_sync('_register_node_class', *args, **kwargs)
    def get_node_class(self, *args, **kwargs):
        return self.execute_sync('get_node_class', *args, **kwargs)
    def get_node_instance(self, *args, **kwargs):
        return self.execute_sync('get_node_instance', *args, **kwargs)
    def _attempt_heuristic_discovery(self, *args, **kwargs):
        return self.execute_sync('_attempt_heuristic_discovery', *args, **kwargs)
    def get_all_nodes_metadata(self, *args, **kwargs):
        return self.execute_sync('get_all_nodes_metadata', *args, **kwargs)

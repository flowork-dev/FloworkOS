########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\neural_knowledge_router\__init__.py total lines 45 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import importlib
import logging
import os
from flowork_kernel.services.base_service import BaseService

class NeuralKnowledgeRouterService(BaseService):
    def __init__(self, kernel, service_id: str):
        self.cells = {}
        if not hasattr(self, 'logger'):
            self.logger = logging.getLogger('KnowledgeHub')
        super().__init__(kernel, service_id)

        self.db = self.kernel.get_service("database_service")
        self.ai_manager = self.kernel.get_service("ai_provider_manager_service")

        self.logger.info("🧠 Neural Knowledge Router Service initialized.")

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
                self.logger.info(f"[KnowledgeHub] ✅ Loaded: {cell_name}.py")
            except Exception as e:
                self.logger.error(f"[KnowledgeHub] ❌ Failed to load '{cell_name}': {e}")
                raise e
        return self.cells[cell_name]

    def add_knowledge(self, *args, **kwargs): return self.execute_sync('add_knowledge', *args, **kwargs)
    def search_knowledge(self, *args, **kwargs): return self.execute_sync('search_knowledge', *args, **kwargs)
    def start(self, *args, **kwargs): return self.execute_sync('start', *args, **kwargs)

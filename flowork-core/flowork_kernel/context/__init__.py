########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\context\__init__.py total lines 77 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import importlib
import logging

class FakeFacRuntime:
    def consume(self, *args, **kwargs): pass
    def remaining(self, *args, **kwargs): return 999999999

class FakeFacEnforcer:
    def permit_run_engine(self, *args, **kwargs): return True

class AgentContext:
    def __init__(self, kernel=None, agent_id=None, session_id=None):
        self.kernel = kernel
        self.agent_id = agent_id
        self.session_id = session_id
        self.cells = {}
        self.logger = logging.getLogger('AgentContext')
        self.fac = FakeFacRuntime()

    def execute_sync(self, cell_name, *args, **kwargs):
        m = self._load_cell(cell_name)
        return m.run(self, *args, **kwargs) if m else None

    async def execute_async(self, cell_name, *args, **kwargs):
        m = self._load_cell(cell_name)
        return await m.run(self, *args, **kwargs) if m else None

    def _load_cell(self, cell_name):
        if cell_name not in self.cells:
            try:
                module = importlib.import_module(f".{cell_name}", package=__package__)
                self.cells[cell_name] = module
            except Exception as e:
                self.logger.error(f"Failed to load context cell {cell_name}: {e}")
                raise e
        return self.cells[cell_name]

    def check(self, *args, **kwargs): return self.execute_sync('check', *args, **kwargs)
    def get_id(self, *args, **kwargs): return self.execute_sync('get_id', *args, **kwargs)
    def consume_gas(self, *args, **kwargs): return self.execute_sync('consume_gas', *args, **kwargs)
    def get_gas_spent(self, *args, **kwargs): return self.execute_sync('get_gas_spent', *args, **kwargs)
    def get_gas_limit(self, *args, **kwargs): return self.execute_sync('get_gas_limit', *args, **kwargs)
    def _enforce_gas(self, *args, **kwargs): return self.execute_sync('_enforce_gas', *args, **kwargs)
    def _enforce_permission(self, *args, **kwargs): return self.execute_sync('_enforce_permission', *args, **kwargs)
    def episodic_read(self, *args, **kwargs): return self.execute_sync('episodic_read', *args, **kwargs)
    def episodic_write(self, *args, **kwargs): return self.execute_sync('episodic_write', *args, **kwargs)

    def knowledge_search(self, query, limit=3):
        """Mencari ingatan jangka panjang AI"""
        router = self.kernel.get_service("neural_knowledge_router")
        user_id = self.kernel.variable_manager.get_variable("current_user_id") or "public"
        return router.execute_sync("search_knowledge", query, user_id, limit=limit)

    def knowledge_index(self, content, source="manual", tags=None):
        """Menyimpan ingatan baru ke AI"""
        router = self.kernel.get_service("neural_knowledge_router")
        user_id = self.kernel.variable_manager.get_variable("current_user_id") or "public"
        return router.execute_sync("add_knowledge", content, user_id, source=source, tags=tags)

    def fs_read(self, *args, **kwargs): return self.execute_sync('fs_read', *args, **kwargs)
    def fs_write(self, *args, **kwargs): return self.execute_sync('fs_write', *args, **kwargs)
    def http_fetch(self, *args, **kwargs): return self.execute_sync('http_fetch', *args, **kwargs)
    def shell_exec(self, *args, **kwargs): return self.execute_sync('shell_exec', *args, **kwargs)
    def boot_agent(self, *args, **kwargs): return self.execute_sync('boot_agent', *args, **kwargs)
    def validate_schema(self, *args, **kwargs): return self.execute_sync('validate_schema', *args, **kwargs)
    def validate_signature(self, *args, **kwargs): return self.execute_sync('validate_signature', *args, **kwargs)
    def validate_ttl(self, *args, **kwargs): return self.execute_sync('validate_ttl', *args, **kwargs)

def boot_agent(kernel, agent_id, session_id):
    ctx = AgentContext(kernel, agent_id, session_id)
    return ctx.boot_agent()

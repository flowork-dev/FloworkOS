########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\agent_executor_service\__init__.py total lines 84 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from flowork_kernel.services.base_service import BaseService
import importlib
import logging
from flowork_kernel.swarm import LocalSwarmRegistry, SwarmCoordinator

class AgentExecutorService(BaseService):
    def __init__(self, kernel, service_id: str):
        self.cells = {}
        if not hasattr(self, 'logger'):
            self.logger = logging.getLogger('LazyHub')

        super().__init__(kernel, service_id)

        self.app_service = self.kernel.get_service('app_service')
        self.workflow_executor = self.kernel.get_service('workflow_executor_service')
        self.ai_manager = self.kernel.get_service('ai_provider_manager_service')
        self.event_bus = self.kernel.get_service('event_bus')

        self.semantic_search = None
        self.sessions = {}
        self.session_locks = {}
        self.active_tasks = {}

        self.local_swarm_registry = LocalSwarmRegistry()
        self.local_swarm_coordinator = SwarmCoordinator(
            send_task_fn=self.local_swarm_registry.make_send_task_fn(),
            default_timeout_s=60.0,
            retries=1,
            backoff_base_s=0.5
        )

        self.gateway_connector = self.kernel.get_service('gateway_connector_service')

        if self.gateway_connector and hasattr(self.gateway_connector, 'send_gateway_swarm_task'):
            self.gateway_swarm_coordinator = SwarmCoordinator(
                send_task_fn=self.gateway_connector.send_gateway_swarm_task,
                default_timeout_s=120.0,
                retries=1,
                backoff_base_s=1.0
            )
            self.logger.info('(R6) Multi-Node Gateway Swarm Coordinator has been initialized.')
        else:
            self.gateway_swarm_coordinator = None
            self.logger.warning("(R6) Multi-Node Swarm disabled: GatewayConnectorService not found or is missing 'send_gateway_swarm_task'.")

        self.logger.debug("Service 'AgentExecutor' initialized with ATOMIC architecture.")

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
            except Exception as e:
                self.logger.error(f"[LazyHub] ❌ Failed to load '{cell_name}': {e}")
                raise e
        return self.cells[cell_name]

    def _get_brain_memory_app(self, *args, **kwargs): return self.execute_sync('_get_brain_memory_app', *args, **kwargs)
    async def start_task(self, *args, **kwargs): return await self.execute_async('start_task', *args, **kwargs)
    async def _run_agent_loop(self, *args, **kwargs): return await self.execute_async('_run_agent_loop', *args, **kwargs)
    async def execute_remote_swarm_task(self, *args, **kwargs): return await self.execute_async('execute_remote_swarm_task', *args, **kwargs)
    def _find_tool_manifest_as_node(self, *args, **kwargs): return self.execute_sync('_find_tool_manifest_as_node', *args, **kwargs)
    def run_dynamic_agent_synchronous(self, *args, **kwargs): return self.execute_sync('run_dynamic_agent_synchronous', *args, **kwargs)
    def _build_agent_tool_list(self, *args, **kwargs): return self.execute_sync('_build_agent_tool_list', *args, **kwargs)
    def _get_tools_prompt_from_manifests(self, *args, **kwargs): return self.execute_sync('_get_tools_prompt_from_manifests', *args, **kwargs)
    def _register_tools_for_swarm(self, *args, **kwargs): return self.execute_sync('_register_tools_for_swarm', *args, **kwargs)
    async def _run_session_logic(self, *args, **kwargs): return await self.execute_async('_run_session_logic', *args, **kwargs)
    async def start_session(self, *args, **kwargs): return await self.execute_async('start_session', *args, **kwargs)
    async def cancel_session(self, *args, **kwargs): return await self.execute_async('cancel_session', *args, **kwargs)
    async def handle_input(self, *args, **kwargs): return await self.execute_async('handle_input', *args, **kwargs)

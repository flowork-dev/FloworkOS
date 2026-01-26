########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\agent_manager_service\agent_manager_service\__init__.py total lines 79 
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
from flowork_kernel.models.AgentModel import AgentModel
import uuid


class AgentManagerService(BaseService):
    STATE_KEY = 'ai_agents'
    def get_all_agents(self) -> list[dict]:
        agents_dict = self.state_manager.get(self.STATE_KEY, {})
        return list(agents_dict.values())
    def get_agent(self, agent_id: str) -> dict | None:
        agents_dict = self.state_manager.get(self.STATE_KEY, {})
        return agents_dict.get(str(agent_id))
    def save_agent(self, agent_data: dict) -> dict:
        try:
            if 'id' not in agent_data or not agent_data['id']:
                agent_data['id'] = str(uuid.uuid4())
            else:
                agent_data['id'] = str(agent_data['id'])
            agent_model = AgentModel(**agent_data)
            agents_dict = self.state_manager.get(self.STATE_KEY, {})
            agents_dict[str(agent_model.id)] = agent_model.model_dump(mode='json')
            self.state_manager.set(self.STATE_KEY, agents_dict)
            self.logger.info(f"Agent '{agent_model.name}' saved with ID {agent_model.id}")
            return agent_model.model_dump(mode='json')
        except Exception as e:
            self.logger.error(f'Failed to save agent: {e}')
            return {'error': str(e)}
    def delete_agent(self, agent_id: str) -> bool:
        agents_dict = self.state_manager.get(self.STATE_KEY, {})
        if agent_id in agents_dict:
            del agents_dict[agent_id]
            self.state_manager.set(self.STATE_KEY, agents_dict)
            self.logger.info(f'Agent with ID {agent_id} has been deleted.')
            return True
        self.logger.warning(f'Attempted to delete non-existent agent with ID {agent_id}.')
        return False

    def __init__(self, kernel, service_id: str):
        self.cells = {}
        if not hasattr(self, 'logger'):
            self.logger = logging.getLogger('LazyHub')
        super().__init__(kernel, service_id)
        self.state_manager = self.kernel.get_service('state_manager')
        self.logger.debug("Service 'AgentManager' initialized.")

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

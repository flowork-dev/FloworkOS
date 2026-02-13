########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\agent_manager_service\save_agent.py total lines 25 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from flowork_kernel.models.AgentModel import AgentModel
import uuid


def run(hub, agent_data: dict) -> dict:
    try:
        if 'id' not in agent_data or not agent_data['id']:
            agent_data['id'] = str(uuid.uuid4())
        else:
            agent_data['id'] = str(agent_data['id'])
        agent_model = AgentModel(**agent_data)
        agents_dict = hub.state_manager.get(hub.STATE_KEY, {})
        agents_dict[str(agent_model.id)] = agent_model.model_dump(mode='json')
        hub.state_manager.set(hub.STATE_KEY, agents_dict)
        hub.logger.info(f"Agent '{agent_model.name}' saved with ID {agent_model.id}")
        return agent_model.model_dump(mode='json')
    except Exception as e:
        hub.logger.error(f'Failed to save agent: {e}')
        return {'error': str(e)}

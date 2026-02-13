########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\agent_manager_service\delete_agent.py total lines 19 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from flowork_kernel.models.AgentModel import AgentModel
import uuid


def run(hub, agent_id: str) -> bool:
    agents_dict = hub.state_manager.get(hub.STATE_KEY, {})
    if agent_id in agents_dict:
        del agents_dict[agent_id]
        hub.state_manager.set(hub.STATE_KEY, agents_dict)
        hub.logger.info(f'Agent with ID {agent_id} has been deleted.')
        return True
    hub.logger.warning(f'Attempted to delete non-existent agent with ID {agent_id}.')
    return False

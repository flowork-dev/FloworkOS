########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\agent_manager_service\get_all_agents.py total lines 13 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from flowork_kernel.models.AgentModel import AgentModel
import uuid


def run(hub) -> list[dict]:
    agents_dict = hub.state_manager.get(hub.STATE_KEY, {})
    return list(agents_dict.values())

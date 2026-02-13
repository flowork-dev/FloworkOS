########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\agent_routes\handle_get_agent.py total lines 22 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from .base_api_route import BaseApiRoute
from aiohttp import web
import json
import asyncio


async def run(hub, request):
    agent_id = request.match_info.get('agent_id')
    agent_manager = hub.service_instance.agent_manager
    if not agent_manager:
        return await hub.execute_async('_json_response', {'error': 'AgentManagerService is not available due to license restrictions.'}, status=503)
    agent = agent_manager.get_agent(agent_id)
    if agent:
        return await hub.execute_async('_json_response', agent)
    else:
        return await hub.execute_async('_json_response', {'error': f"Agent with ID '{agent_id}' not found."}, status=404)

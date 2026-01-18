########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\agent_routes\handle_get_agent_run_status.py total lines 22 
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
    run_id = request.match_info.get('run_id')
    agent_executor = hub.service_instance.agent_executor
    if not agent_executor:
        return await hub.execute_async('_json_response', {'error': 'AgentExecutorService is not available due to license restrictions.'}, status=503)
    status = agent_executor.get_run_status(run_id)
    if 'error' in status:
        return await hub.execute_async('_json_response', status, status=404)
    else:
        return await hub.execute_async('_json_response', status)

########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\agent_routes\handle_run_agent_task_adhoc.py total lines 30 
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
    agent_executor = hub.service_instance.agent_executor
    if not agent_executor:
        return await hub.execute_async('_json_response', {'error': 'AgentExecutorService unavailable.'}, status=503)
    try:
        body = await request.json()
        instruction = body.get('instruction') or body.get('user_instruction')
        tools = body.get('tools', [])
        user_id = getattr(request, 'user_id', 'anonymous_dev')
        if not instruction:
            return await hub.execute_async('_json_response', {'error': "Missing 'instruction'."}, status=400)
        if hasattr(agent_executor, 'start_task'):
            task_id = await agent_executor.start_task(instruction, tools, user_id=user_id)
            return await hub.execute_async('_json_response', {'status': 'started', 'task_id': task_id}, status=202)
        else:
            return await hub.execute_async('_json_response', {'error': "Engine update required: AgentExecutor missing 'start_task'."}, status=501)
    except Exception as e:
        return await hub.execute_async('_json_response', {'error': str(e)}, status=500)

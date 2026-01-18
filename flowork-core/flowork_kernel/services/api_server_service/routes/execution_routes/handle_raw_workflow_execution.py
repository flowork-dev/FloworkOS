########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\execution_routes\handle_raw_workflow_execution.py total lines 33 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from .base_api_route import BaseApiRoute
import time
import asyncio
import uuid
import traceback


async def run(hub, request):
    try:
        body = await request.json()
        nodes = body.get('nodes')
        connections = body.get('connections')
        initial_payload = body.get('initial_payload', {'triggered_by': 'raw_api_call'})
        start_node_id = body.get('start_node_id')
        mode = body.get('mode', 'EXECUTE')
        if nodes is None or connections is None:
            return await hub.execute_async('_json_response', {'error': "Request body must contain 'nodes' and 'connections'."}, status=400)
        await hub.execute_async('logger', f"API call received to execute raw workflow in '{mode}' mode.", 'INFO')
        user_context = request.get('user_context', None)
        job_id = await hub.service_instance.trigger_workflow_by_api(preset_name='raw_execution_from_canvas', initial_payload=initial_payload, raw_workflow_data={'nodes': nodes, 'connections': connections}, start_node_id=start_node_id, mode=mode, user_context=user_context)
        if job_id:
            return await hub.execute_async('_json_response', {'status': 'accepted', 'message': 'Raw workflow has been queued for execution.', 'job_id': job_id}, status=202)
        else:
            return await hub.execute_async('_json_response', {'status': 'error', 'message': 'Failed to queue the raw workflow.'}, status=500)
    except Exception as e:
        await hub.execute_async('logger', f'Error handling raw workflow execution: {e}', 'CRITICAL')
        return await hub.execute_async('_json_response', {'error': f'Internal Server Error: {e}'}, status=500)

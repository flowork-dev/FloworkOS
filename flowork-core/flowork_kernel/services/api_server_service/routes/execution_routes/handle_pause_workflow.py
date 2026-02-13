########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\execution_routes\handle_pause_workflow.py total lines 20 
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
    job_id = request.match_info.get('job_id')
    executor = hub.service_instance.workflow_executor
    if not executor:
        return await hub.execute_async('_json_response', {'error': 'WorkflowExecutorService is not available.'}, status=503)
    executor.pause_execution()
    return await hub.execute_async('_json_response', {'status': 'success', 'message': f'Pause signal sent to the current workflow.'})

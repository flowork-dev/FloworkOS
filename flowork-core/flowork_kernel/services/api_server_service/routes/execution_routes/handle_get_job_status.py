########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\execution_routes\handle_get_job_status.py total lines 22 
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
    if not job_id:
        return await hub.execute_async('_json_response', {'error': 'Job ID is required.'}, status=400)
    status_data = hub.service_instance.get_job_status(job_id)
    if status_data:
        return await hub.execute_async('_json_response', status_data)
    else:
        return await hub.execute_async('_json_response', {'error': f"Job with ID '{job_id}' not found."}, status=404)

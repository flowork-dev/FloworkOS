########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\execution_routes\handle_scan_execution.py total lines 26 
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
    scanner_id = request.match_info.get('scanner_id')
    try:
        log_target = 'ALL' if not scanner_id else scanner_id
        await hub.execute_async('logger', f'API call received to execute diagnostics scan for: {log_target}.', 'INFO')
        job_id = hub.service_instance.trigger_scan_by_api(scanner_id)
        if job_id:
            return await hub.execute_async('_json_response', {'status': 'accepted', 'message': f"System diagnostics scan for '{log_target}' has been queued.", 'job_id': job_id}, status=202)
        else:
            return await hub.execute_async('_json_response', {'status': 'error', 'message': 'Failed to start diagnostics scan.'}, status=500)
    except Exception as e:
        await hub.execute_async('logger', f'Error handling API scan execution: {e}', 'ERROR')
        return await hub.execute_async('_json_response', {'error': f'Internal Server Error: {e}'}, status=500)

########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\engine_routes\handle_cancel_schedule.py total lines 38 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import datetime
import time
import json
from .base_api_route import BaseApiRoute
from flowork_kernel.exceptions import PermissionDeniedError
from collections import Counter, defaultdict
from flowork_kernel.singleton import Singleton
from flowork_kernel.services.database_service.database_service import DatabaseService


async def run(hub, request):
    try:
        permission_manager = hub.kernel.get_service('permission_manager_service', is_system_call=True)
        if permission_manager:
            permission_manager.check_permission('engine_management')
        body = await request.json()
        task_name = body.get('task_name')
        if not task_name:
            return await hub.execute_async('_json_response', {'error': 'Missing task_name'}, status=400)
        scheduler_app = hub.os_scheduler
        if not scheduler_app:
            return await hub.execute_async('_json_response', {'error': 'Scheduler App is not available.'}, status=503)
        success = scheduler_app.cancel_task(task_name)
        if success:
            return await hub.execute_async('_json_response', {'status': 'success', 'message': f"Task '{task_name}' cancelled successfully."}, status=200)
        else:
            return await hub.execute_async('_json_response', {'error': f"Failed to cancel task '{task_name}'. It may have already run or does not exist."}, status=404)
    except PermissionDeniedError as e:
        return await hub.execute_async('_json_response', {'error': str(e)}, status=403)
    except Exception as e:
        await hub.execute_async('logger', f'Error handling cancel schedule action: {e}', 'CRITICAL')
        return await hub.execute_async('_json_response', {'error': f'Internal Server Error: {e}'}, status=500)

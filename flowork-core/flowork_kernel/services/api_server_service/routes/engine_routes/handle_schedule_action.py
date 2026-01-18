########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\engine_routes\handle_schedule_action.py total lines 41 
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
        action_type = body.get('action_type')
        timestamp_str = body.get('timestamp')
        task_name = body.get('task_name')
        if not all([action_type, timestamp_str, task_name]):
            return await hub.execute_async('_json_response', {'error': 'Missing action_type, timestamp, or task_name'}, status=400)
        scheduled_dt = datetime.datetime.fromisoformat(timestamp_str)
        scheduler_app = hub.os_scheduler
        if not scheduler_app:
            return await hub.execute_async('_json_response', {'error': 'Scheduler App (system_scheduler) is not installed or available.'}, status=503)
        success = scheduler_app.schedule_action(action_type, scheduled_dt, task_name)
        if success:
            return await hub.execute_async('_json_response', {'status': 'success', 'message': f"Action '{action_type}' scheduled successfully via App."}, status=202)
        else:
            return await hub.execute_async('_json_response', {'error': 'App failed to schedule action.'}, status=500)
    except PermissionDeniedError as e:
        return await hub.execute_async('_json_response', {'error': str(e)}, status=403)
    except Exception as e:
        await hub.execute_async('logger', f'Error handling schedule action: {e}', 'CRITICAL')
        return await hub.execute_async('_json_response', {'error': f'Internal Server Error: {e}'}, status=500)

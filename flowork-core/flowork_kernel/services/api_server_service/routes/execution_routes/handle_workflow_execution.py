########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\execution_routes\handle_workflow_execution.py total lines 48 
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
    preset_name = request.match_info.get('preset_name')
    if not preset_name:
        return await hub.execute_async('_json_response', {'error': 'Preset name is required for execution.'}, status=400)
    if not hub.kernel.is_tier_sufficient('basic'):
        COOLDOWN_SECONDS = 300
        state_manager = hub.service_instance.state_manager
        if state_manager:
            user_context = request.get('user_context', None)
            user_id = user_context.get('user_id') if user_context else 'public'
            last_call_timestamp = state_manager.get('api_last_call_timestamp_free_tier', user_id=user_id, default=0)
            current_time = time.time()
            if current_time - last_call_timestamp < COOLDOWN_SECONDS:
                remaining_time = int(COOLDOWN_SECONDS - (current_time - last_call_timestamp))
                error_message = f'API call limit for Free tier. Please wait {remaining_time} seconds.'
                await hub.execute_async('logger', error_message, 'WARN')
                return await hub.execute_async('_json_response', {'status': 'error', 'message': error_message}, status=429)
    try:
        body = await request.json()
        initial_payload = body if body is not None else {'triggered_by': 'api'}
        await hub.execute_async('logger', f"API call received to execute preset '{preset_name}'.", 'INFO')
        user_context = request.get('user_context', None)
        if not hub.kernel.is_tier_sufficient('basic'):
            state_manager = hub.service_instance.state_manager
            if state_manager:
                user_id = user_context.get('user_id') if user_context else 'public'
                state_manager.set('api_last_call_timestamp_free_tier', time.time(), user_id=user_id)
        job_id = await hub.service_instance.trigger_workflow_by_api(preset_name, initial_payload, user_context=user_context)
        if job_id:
            return await hub.execute_async('_json_response', {'status': 'accepted', 'message': f"Workflow for preset '{preset_name}' has been queued.", 'job_id': job_id}, status=202)
        else:
            return await hub.execute_async('_json_response', {'status': 'error', 'message': f"Preset '{preset_name}' not found."}, status=404)
    except Exception as e:
        await hub.execute_async('logger', f"Error handling API execution for '{preset_name}': {e}", 'ERROR')
        return await hub.execute_async('_json_response', {'error': f'Internal Server Error: {e}'}, status=500)

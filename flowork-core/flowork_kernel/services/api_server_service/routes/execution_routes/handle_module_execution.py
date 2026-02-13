########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\execution_routes\handle_module_execution.py total lines 70 
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
    """
        Handles direct module execution.
        FIX: Increased timeout to 300s.
        FIX: Added direct DB Polling via executor.get_monitor_status()
        """
    try:
        body = await request.json()
        module_id = body.get('module_id')
        params = body.get('params', {})
        if not module_id:
            return await hub.execute_async('_json_response', {'error': 'module_id is required'}, status=400)
        node_id = f'exec_node_{uuid.uuid4().hex[:8]}'
        nodes = [{'id': node_id, 'component_id': module_id, 'type': 'module', 'position': {'x': 0, 'y': 0}, 'properties': params}]
        await hub.execute_async('logger', f'[Execution] Direct run request for: {module_id}', 'INFO')
        execution_payload = {'inputs': params}
        job_id = await hub.service_instance.trigger_workflow_by_api(preset_name=module_id, initial_payload=execution_payload, raw_workflow_data={'nodes': nodes, 'connections': []}, start_node_id=node_id, mode='EXECUTE', user_context=request.get('user_context', None))
        if not job_id:
            await hub.execute_async('logger', f'[Execution] Failed to get Job ID.', 'ERROR')
            return await hub.execute_async('_json_response', {'error': 'Failed to queue execution'}, status=500)
        start_time = time.time()
        timeout_limit = 300
        while time.time() - start_time < timeout_limit:
            status_data = hub.service_instance.get_job_status(job_id)
            state = status_data.get('status') if status_data else 'unknown'
            if state not in ['completed', 'SUCCEEDED', 'failed', 'FAILED']:
                executor = hub.service_instance.workflow_executor
                if executor and hasattr(executor, 'get_monitor_status'):
                    db_status = executor.get_monitor_status(job_id)
                    if db_status:
                        status_data = db_status
                        state = db_status.get('status')
            if state == 'completed' or state == 'SUCCEEDED':
                result_payload = status_data.get('result', {})
                if not result_payload:
                    history = status_data.get('history', {})
                    steps = history.get('steps', [])
                    for step in steps:
                        if step.get('node_id') == node_id:
                            result_payload = step.get('output_payload', {})
                            break
                final_payload = result_payload
                if isinstance(result_payload, dict):
                    if 'payload' in result_payload:
                        final_payload = result_payload['payload']
                    elif 'data' in result_payload:
                        final_payload = result_payload['data']
                return await hub.execute_async('_json_response', {'status': 'success', 'output_name': 'success', 'payload': final_payload, 'job_id': job_id})
            elif state == 'failed' or state == 'error' or state == 'FAILED':
                error_msg = status_data.get('error', 'Unknown execution error')
                return await hub.execute_async('_json_response', {'status': 'error', 'message': error_msg, 'job_id': job_id}, status=500)
            await asyncio.sleep(1.0)
        return await hub.execute_async('_json_response', {'status': 'timeout', 'message': f'Execution timed out after {timeout_limit}s waiting for result', 'job_id': job_id}, status=504)
    except Exception as e:
        traceback.print_exc()
        await hub.execute_async('logger', f'Module execution CRITICAL error: {e}', 'CRITICAL')
        return await hub.execute_async('_json_response', {'error': str(e)}, status=500)

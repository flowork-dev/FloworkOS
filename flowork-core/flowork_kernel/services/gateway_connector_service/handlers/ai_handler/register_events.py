########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\gateway_connector_service\handlers\ai_handler\register_events.py total lines 194 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from flowork_kernel.services.gateway_connector_service.handlers.base_handler import BaseHandler, CURRENT_PAYLOAD_VERSION

import asyncio
from flowork_kernel.fac_enforcer import FacRuntime
from flowork_kernel.exceptions import PermissionDeniedError
from flowork_kernel.services.gateway_connector_service.handlers.base_handler import BaseHandler


def run(hub):

    @hub.sio.event(namespace='/engine-socket')
    async def gw_start_session(data):
        session_id = data.get('session_id')
        engine_id = data.get('engine_id')
        fac_dict = data.get('fac')
        hub.logger.info(f"[Core] Received 'gw:start_session' from Gateway for session: {session_id}")
        try:
            if not all([session_id, engine_id, fac_dict]):
                hub.logger.warning(f"[Auth] 'gw:start_session' missing session_id, engine_id, or fac.")
                raise PermissionDeniedError('Invalid start payload (missing session_id, engine_id, or fac)')
            fac_rt = FacRuntime(fac_dict)
            fac_rt.permit_run_engine(engine_id_to_run=engine_id)
            hub.service.g_active_sessions[session_id] = fac_rt
            hub.logger.info(f'FAC Validated. Storing runtime for session {session_id}.')
            agent_executor = hub.service.kernel_services.get('agent_executor_service')
            if not agent_executor:
                hub.logger.error("[Core] CRITICAL: 'agent_executor_service' not found in kernel_services. Cannot start session.")
                await hub.service.emit_to_gateway('core:agent_error', {'session_id': data.get('session_id'), 'code': 'SERVICE_NOT_FOUND', 'message': 'AgentExecutorService is not running on this Core engine.'})
                return
            asyncio.create_task(agent_executor.start_session(data, hub.service.emit_to_gateway, fac_rt=fac_rt))
            await hub.service.emit_to_gateway('core:agent_ack', {'type': 'ack', 'corr': 'start', 'session_id': data.get('session_id')})
        except (PermissionError, PermissionDeniedError, ValueError) as e:
            hub.logger.error(f'[Core] FAC Validation FAILED for session {session_id}: {e}', exc_info=False)
            await hub.service.emit_to_gateway('core:agent_error', {'session_id': data.get('session_id'), 'code': 'FAC_INVALID', 'message': f'Session rejected: {e}'})
        except Exception as e:
            hub.logger.error(f"[Core] Error processing 'gw:start_session': {e}", exc_info=True)
            try:
                await hub.service.emit_to_gateway('core:agent_error', {'session_id': data.get('session_id'), 'code': 'START_EXCEPTION', 'message': f'Core engine failed to start session: {e}'})
            except Exception as e2:
                hub.logger.error(f'[Core] Failed to even send the error back: {e2}')

    @hub.sio.event(namespace='/engine-socket')
    async def gw_cancel_session(data):
        session_id = data.get('session_id')
        hub.logger.info(f"[Core] Received 'gw:cancel_session' from Gateway for session: {session_id}")
        if session_id in hub.service.g_active_sessions:
            del hub.service.g_active_sessions[session_id]
            hub.logger.info(f'[Core] Removed active FAC runtime for cancelled session {session_id}.')
        try:
            agent_executor = hub.service.kernel_services.get('agent_executor_service')
            if not agent_executor:
                hub.logger.error(f"[Core] 'agent_executor_service' not found. Cannot cancel session {session_id}.")
                return
            asyncio.create_task(agent_executor.cancel_session(data))
            await hub.service.emit_to_gateway('core:agent_ack', {'type': 'ack', 'corr': 'cancel', 'session_id': session_id})
        except Exception as e:
            hub.logger.error(f"[Core] Error processing 'gw:cancel_session': {e}", exc_info=True)

    @hub.sio.event(namespace='/engine-socket')
    async def gw_agent_input(data):
        session_id = data.get('session_id')
        hub.logger.info(f"[Core] Received 'gw:agent_input' from Gateway for session: {session_id}")
        fac_rt = hub.service.g_active_sessions.get(session_id)
        if not fac_rt:
            hub.logger.warning(f'[Core] Input for {session_id} rejected: No valid FAC runtime found. (Session may have expired or failed start).')
            await hub.service.emit_to_gateway('core:agent_error', {'session_id': session_id, 'code': 'SESSION_INVALID', 'message': 'No valid session runtime found. Please restart session.'})
            return
        try:
            agent_executor = hub.service.kernel_services.get('agent_executor_service')
            if not agent_executor:
                hub.logger.error(f"[Core] 'agent_executor_service' not found. Cannot process input for {session_id}.")
                await hub.service.emit_to_gateway('core:agent_error', {'session_id': session_id, 'code': 'SERVICE_NOT_FOUND', 'message': 'AgentExecutorService is not running on this Core engine.'})
                return
            asyncio.create_task(agent_executor.handle_input(data))
            await hub.service.emit_to_gateway('core:agent_ack', {'type': 'ack', 'corr': 'input', 'session_id': session_id})
        except (PermissionError, PermissionDeniedError) as e:
            hub.logger.error(f"[Core] Budget Error processing 'gw:agent_input' for {session_id}: {e}", exc_info=True)
            await hub.service.emit_to_gateway('core:agent_error', {'session_id': session_id, 'code': 'BUDGET_EXCEEDED', 'message': f'Input rejected: {e}'})
        except Exception as e:
            hub.logger.error(f"[Core] Error processing 'gw:agent_input': {e}", exc_info=True)
            try:
                await hub.service.emit_to_gateway('core:agent_error', {'session_id': session_id, 'code': 'INPUT_EXCEPTION', 'message': f'Core engine failed to process input: {e}'})
            except Exception as e2:
                hub.logger.error(f'[Core] Failed to even send the input error back: {e2}')

    @hub.sio.event(namespace='/engine-socket')
    async def gateway_execute_swarm_task(data):
        task_payload = data.get('task_payload', {})
        task_id = task_payload.get('task_id')
        if not task_id:
            hub.logger.error(f"[Gateway R6] Received 'gateway_execute_swarm_task' with no task_id. Ignoring.")
            return
        hub.logger.info(f'[Gateway R6] Received task {task_id} from Gateway. Executing...')
        agent_executor = hub.service.kernel_services.get('agent_executor_service')
        if not agent_executor:
            hub.logger.error(f'[Gateway R6] Cannot execute task {task_id}: AgentExecutorService not found.')
            result = {'error': 'EngineError: AgentExecutorService not found.'}
        else:
            try:
                result = await agent_executor.execute_remote_swarm_task(task_payload)
            except Exception as e:
                hub.logger.error(f'[Gateway R6] Execution of task {task_id} FAILED: {e}', exc_info=True)
                result = {'error': f'EngineError: {e}'}
        hub.logger.info(f'[Gateway R6] Execution for {task_id} complete. Sending result back to Gateway.')
        await hub.service.emit_to_gateway('core:swarm_task_result', {'task_id': task_id, 'result': result})

    @hub.sio.event(namespace='/engine-socket')
    async def gateway_swarm_task_result(data):
        task_id = data.get('task_id')
        result = data.get('result', {})
        if not task_id:
            hub.logger.error(f"[Gateway R6] Received 'gateway_swarm_task_result' with no task_id. Dropping.")
            return
        hub.logger.info(f'[Gateway R6] Received result for *our* pending task: {task_id}')
        async with hub.service._pending_swarm_tasks_lock:
            task_future = hub.service._pending_swarm_tasks.get(task_id)
        if task_future and (not task_future.done()):
            task_future.set_result(result)
        else:
            hub.logger.warning(f'[Gateway R6] Received result for unknown or already-timed-out task {task_id}. Ignoring.')

    @hub.sio.event(namespace='/engine-socket')
    async def request_local_models(data):
        if not isinstance(data, dict) or data.get('v') != CURRENT_PAYLOAD_VERSION:
            return
        real_data = data.get('payload', {})
        user_id = real_data.get('user_context', {}).get('id')
        hub.logger.info(f"Received 'request_local_models' from user {user_id}")
        models_list = []
        error_msg = None
        try:
            ai_manager = hub.service.kernel_services.get('ai_provider_manager_service')
            if ai_manager:
                models_list = [{'id': model_id, 'name': model_data.get('name', model_id)} for (model_id, model_data) in ai_manager.local_models.items() if model_data.get('category') == 'text']
            else:
                error_msg = 'AIProviderManagerService not found.'
        except Exception as e:
            error_msg = str(e)
        versioned_response = {'v': CURRENT_PAYLOAD_VERSION, 'payload': {'models': models_list, 'error': error_msg, '_target_user_id': user_id}}
        await hub.sio.emit('response_local_models', versioned_response, namespace='/engine-socket')

    @hub.sio.event(namespace='/engine-socket')
    async def start_training_job(data):
        if not isinstance(data, dict) or data.get('v') != CURRENT_PAYLOAD_VERSION:
            return
        real_data = data.get('payload', {})
        user_id = real_data.get('user_context', {}).get('id')
        config = real_data.get('config')
        hub.logger.info(f"Received 'start_training_job' from user {user_id} for {config.get('new_model_name')}")
        job_response = None
        try:
            training_service = hub.execute_sync('_get_app_instance', 'neural_trainer')
            if training_service:
                job_response = training_service.start_fine_tuning_job(base_model_id=config.get('base_model_id'), dataset_name=config.get('dataset_name'), new_model_name=config.get('new_model_name'), training_args=config.get('training_args', {}))
                await hub.execute_sync('_send_training_status', user_id)
            else:
                raise Exception('Neural Trainer App is not installed.')
        except Exception as e:
            hub.logger.error(f"[Core] Error processing 'start_training_job': {e}", exc_info=True)

    @hub.sio.event(namespace='/engine-socket')
    async def request_training_job_status(data):
        if not isinstance(data, dict) or data.get('v') != CURRENT_PAYLOAD_VERSION:
            return
        real_data = data.get('payload', {})
        user_id = real_data.get('user_context', {}).get('id')
        await hub.execute_sync('_send_training_status', user_id)

    async def _send_training_status(self, user_id):
        """ Helper to avoid code duplication since it is called from two places """
        hub.logger.info(f"Received 'request_training_job_status' from user {user_id}")
        jobs_list = []
        error_msg = None
        try:
            training_service = hub.execute_sync('_get_app_instance', 'neural_trainer')
            if training_service:
                if hasattr(training_service, 'list_training_jobs'):
                    jobs_list = training_service.list_training_jobs()
                else:
                    jobs_list = list(training_service.training_jobs.values())
            else:
                error_msg = 'Neural Trainer App is not available.'
        except Exception as e:
            error_msg = str(e)
            hub.logger.error(f"[Core] Error processing 'request_training_job_status': {e}", exc_info=True)
        versioned_response = {'v': CURRENT_PAYLOAD_VERSION, 'payload': {'jobs': jobs_list, 'error': error_msg, '_target_user_id': user_id}}
        await hub.sio.emit('response_training_job_status', versioned_response, namespace='/engine-socket')
        hub.logger.info(f"Sent 'response_training_job_status' to user {user_id}")

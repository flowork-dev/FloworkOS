########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\gateway_connector_service\handlers\ai_handler\_send_training_status.py total lines 32 
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


async def run(hub, user_id):
    """ [GEMINI NOTE] Redundant method found in source, maintaining for Rule 2 but pointing to same App logic """
    hub.logger.info(f"Received 'request_training_job_status' from user {user_id}")
    jobs_list = []
    error_msg = None
    try:
        training_service = await hub.execute_async('_get_app_instance', 'neural_trainer')
        if training_service:
            if hasattr(training_service, 'list_training_jobs'):
                jobs_list = training_service.list_training_jobs()
            else:
                jobs_list = list(training_service.training_jobs.values())
        else:
            error_msg = 'Neural Trainer App not found.'
    except Exception as e:
        error_msg = str(e)
    versioned_response = {'v': CURRENT_PAYLOAD_VERSION, 'payload': {'jobs': jobs_list, 'error': error_msg, '_target_user_id': user_id}}
    await hub.sio.emit('response_training_job_status', versioned_response, namespace='/engine-socket')

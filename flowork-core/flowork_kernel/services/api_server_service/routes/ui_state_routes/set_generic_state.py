########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\ui_state_routes\set_generic_state.py total lines 25 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from .base_api_route import BaseApiRoute
import threading


async def run(hub, request):
    key = request.match_info['key']
    state_manager = hub.kernel.get_service('state_manager', is_system_call=True)
    user_id = request.get('user_context', {}).get('user_id')
    if not state_manager:
        return await hub.execute_async('_json_response', {'error': 'State manager not available'}, status=500)
    data = await request.json()
    if key == 'current_user_data':
        await hub.execute_async('logger', 'Received user data from Gateway, updating Kernel state...', 'INFO', source='ApiServer')
        hub.kernel.current_user = data
        state_manager.set('gateway_injected_user_data', data, user_id=user_id)
        await hub.execute_async('logger', 'Saved user data to persistent state for recovery after restart.', 'DEBUG', 'ApiServer')
        await hub.execute_async('_update_permissions_synchronous', data)
    state_manager.set(key, data, user_id=user_id)
    return await hub.execute_async('_json_response', {'status': 'success'})

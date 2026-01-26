########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\settings_routes\handle_patch_settings.py total lines 24 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from .base_api_route import BaseApiRoute


async def run(hub, request):
    """
        Updates settings via StateManager.
        """
    state_manager = hub.service_instance.kernel.get_service('state_manager_service')
    if not state_manager:
        return await hub.execute_async('_json_response', {'error': 'StateManager service is unavailable.'}, status=503)
    try:
        body = await request.json()
        if not body:
            return await hub.execute_async('_json_response', {'error': 'Empty payload'}, status=400)
        state_manager.update_all(body)
        return await hub.execute_async('_json_response', {'status': 'success', 'message': 'Settings updated.', 'settings': state_manager.get_all()})
    except Exception as e:
        return await hub.execute_async('_json_response', {'error': f'Failed to update settings: {str(e)}'}, status=500)

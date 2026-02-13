########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\settings_routes\handle_get_settings.py total lines 18 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from .base_api_route import BaseApiRoute


async def run(hub, request):
    """
        Retrieves global settings from StateManager.
        """
    state_manager = hub.service_instance.kernel.get_service('state_manager_service')
    if not state_manager:
        return await hub.execute_async('_json_response', {'error': 'StateManager service is unavailable.'}, status=503)
    settings = state_manager.get_all()
    return await hub.execute_async('_json_response', settings)

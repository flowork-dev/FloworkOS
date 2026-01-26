########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\variable_routes\handle_get_variables.py total lines 22 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from aiohttp import web
from flowork_kernel.singleton import Singleton

async def run(hub, request):
    variable_manager = Singleton.get_instance('variable_manager')

    if not variable_manager and hasattr(hub, 'kernel') and hasattr(hub.kernel, 'services'):
         variable_manager = hub.kernel.services.get('variable_manager_service')

    if not variable_manager:
        return web.json_response({'error': 'VariableManager service is unavailable.'}, status=503)

    user_id = request.headers.get('x-user-id')
    all_vars = variable_manager.get_all_variables_for_api(user_id=user_id)

    return web.json_response(all_vars)

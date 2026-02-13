########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\variable_routes\handle_put_variable.py total lines 46 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from aiohttp import web
from flowork_kernel.singleton import Singleton

async def run(hub, request):
    variable_name = request.match_info.get('variable_name')

    variable_manager = Singleton.get_instance('variable_manager')

    if not variable_manager:
        if hasattr(hub, 'service_instance') and hasattr(hub.service_instance, 'variable_manager'):
             variable_manager = hub.service_instance.variable_manager

        elif hasattr(hub, 'kernel') and hasattr(hub.kernel, 'services'):
             variable_manager = hub.kernel.services.get('variable_manager_service')

    if not variable_manager:
        hub.logger.error("❌ VariableManager NOT FOUND in Singleton or Kernel!")
        return web.json_response({'error': 'VariableManager service is unavailable.'}, status=503)

    try:
        body = await request.json()
    except:
        return web.json_response({'error': 'Invalid JSON body'}, status=400)

    value = body.get('value')
    is_secret = body.get('is_secret', False)
    is_enabled = body.get('is_enabled', True)
    mode = body.get('mode', 'single')

    try:
        user_id = request.headers.get('x-user-id')

        variable_manager.set_variable(variable_name, value, user_id=user_id, is_secret=is_secret)

        return web.json_response({'status': 'success', 'message': f"Variable '{variable_name}' saved."}, status=200)
    except ValueError as e:
        return web.json_response({'error': str(e)}, status=400)
    except Exception as e:
        hub.logger.error(f"Error saving variable: {e}")
        return web.json_response({'error': str(e)}, status=500)

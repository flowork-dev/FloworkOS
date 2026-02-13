########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\variable_routes\handle_patch_variable_state.py total lines 26 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from .base_api_route import BaseApiRoute


async def run(hub, request):
    variable_name = request.match_info.get('variable_name')
    variable_manager = hub.service_instance.variable_manager
    if not variable_manager:
        return await hub.execute_async('_json_response', {'error': 'VariableManager service is unavailable.'}, status=503)
    body = await request.json()
    if 'enabled' not in body or not isinstance(body['enabled'], bool):
        return await hub.execute_async('_json_response', {'error': "Request body must contain a boolean 'enabled' key."}, status=400)
    is_enabled = body['enabled']
    user_context = request.get('user_context', {})
    user_id = user_context.get('user_id')
    success = variable_manager.set_variable_enabled_state(variable_name, is_enabled, user_id=user_id)
    if success:
        action = 'enabled' if is_enabled else 'disabled'
        return await hub.execute_async('_json_response', {'status': 'success', 'message': f"Variable '{variable_name}' has been {action}."}, status=200)
    else:
        return await hub.execute_async('_json_response', {'error': f"Variable '{variable_name}' not found."}, status=404)

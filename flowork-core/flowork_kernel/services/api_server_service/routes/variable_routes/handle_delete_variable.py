########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\variable_routes\handle_delete_variable.py total lines 22 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from aiohttp import web

async def run(hub, request):
    variable_name = request.match_info.get('variable_name')
    variable_manager = hub.kernel.variable_manager

    if not variable_manager:
        return web.json_response({'error': 'VariableManager service is unavailable.'}, status=503)

    user_id = request.headers.get('x-user-id')

    try:
        variable_manager.delete_variable(variable_name, user_id=user_id)
        return web.json_response(None, status=204)
    except Exception as e:
        return web.json_response({'error': str(e)}, status=404)

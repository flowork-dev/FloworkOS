########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\preset_routes\handle_get_specific_preset_version.py total lines 24 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from .base_api_route import BaseApiRoute


async def run(hub, request):
    preset_name = request.match_info.get('preset_name')
    version_filename = request.match_info.get('version_filename')
    preset_manager = hub.service_instance.preset_manager
    if not preset_manager:
        return await hub.execute_async('_json_response', {'error': 'PresetManager service is unavailable.'}, status=503)
    user_context = request.get('user_context', {})
    user_id = user_context.get('user_id')
    if not user_id:
        return await hub.execute_async('_json_response', {'error': 'User context is missing.'}, status=401)
    version_data = preset_manager.load_preset_version(preset_name, version_filename, user_id=user_id)
    if version_data:
        return await hub.execute_async('_json_response', version_data)
    else:
        return await hub.execute_async('_json_response', {'error': f"Version '{version_filename}' for preset '{preset_name}' not found."}, status=404)

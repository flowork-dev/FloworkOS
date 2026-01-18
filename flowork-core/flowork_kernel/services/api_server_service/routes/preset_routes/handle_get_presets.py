########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\preset_routes\handle_get_presets.py total lines 26 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from .base_api_route import BaseApiRoute


async def run(hub, request):
    preset_manager = hub.service_instance.preset_manager
    if not preset_manager:
        await hub.execute_async('logger', 'Gracefully handling missing PresetManager service.', 'INFO')
        return await hub.execute_async('_json_response', [])
    user_context = request.get('user_context', {})
    user_id = user_context.get('user_id')
    if not user_id:
        return await hub.execute_async('_json_response', {'error': 'User context is missing, cannot fetch user-specific data.'}, status=401)
    preset_list = preset_manager.get_preset_list(user_id=user_id)
    loc = hub.service_instance.loc
    core_files = hub.service_instance.core_component_ids
    response_data = []
    for item in preset_list:
        name = item.get('name')
        response_data.append({'id': name, 'name': name.replace('_', ' ').replace('-', ' '), 'version': 'N/A', 'is_paused': False, 'description': loc.get('marketplace_preset_desc', fallback='Workflow Preset File') if loc else 'Workflow Preset File', 'is_core': name in core_files, 'tier': 'N/A'})
    return await hub.execute_async('_json_response', sorted(response_data, key=lambda x: x['name']))

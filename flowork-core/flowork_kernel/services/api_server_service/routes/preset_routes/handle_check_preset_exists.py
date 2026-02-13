########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\preset_routes\handle_check_preset_exists.py total lines 27 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from .base_api_route import BaseApiRoute


async def run(hub, request):
    preset_name = request.match_info.get('preset_name')
    user_context = request.get('user_context', {})
    user_id = user_context.get('user_id')
    if not preset_name or not user_id:
        return await hub.execute_async('_json_response', {'error': 'Preset name and user context are required.'}, status=400)
    preset_manager = hub.service_instance.preset_manager
    if not preset_manager:
        await hub.execute_async('logger', 'PresetRoutes: PresetManagerService not available.', 'ERROR')
        return await hub.execute_async('_json_response', {'error': 'Preset manager service unavailable.'}, status=503)
    await hub.execute_async('logger', f"PresetRoutes: Checking existence of preset '{preset_name}' for user '{user_id[:8]}...'", 'DEBUG')
    preset_data = preset_manager.get_preset_data(preset_name, user_id=user_id)
    if preset_data:
        await hub.execute_async('logger', f"PresetRoutes: Preset '{preset_name}' found for user '{user_id[:8]}...'", 'INFO')
        return await hub.execute_async('_json_response', {'exists': True})
    else:
        await hub.execute_async('logger', f"PresetRoutes: Preset '{preset_name}' NOT found for user '{user_id[:8]}...'", 'WARN')
        return await hub.execute_async('_json_response', {'exists': False}, status=404)

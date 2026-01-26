########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\preset_routes\handle_post_presets.py total lines 28 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from .base_api_route import BaseApiRoute


async def run(hub, request):
    preset_manager = hub.service_instance.preset_manager
    if not preset_manager:
        return await hub.execute_async('_json_response', {'error': 'PresetManager service is unavailable.'}, status=503)
    body = await request.json()
    preset_name = body.get('name')
    workflow_data = body.get('workflow_data')
    signature = body.get('signature')
    if not preset_name or not workflow_data or (not signature):
        return await hub.execute_async('_json_response', {'error': "Request body must contain 'name', 'workflow_data', and 'signature'."}, status=400)
    user_context = request.get('user_context', {})
    user_id = user_context.get('user_id')
    if not user_id:
        return await hub.execute_async('_json_response', {'error': 'User context is missing, cannot save preset.'}, status=401)
    save_success = preset_manager.save_preset(preset_name, workflow_data, user_id=user_id, signature=signature)
    if save_success:
        return await hub.execute_async('_json_response', {'status': 'success', 'message': f"Preset '{preset_name}' created/updated."}, status=201)
    else:
        return await hub.execute_async('_json_response', {'error': f"Failed to save preset '{preset_name}'."}, status=500)

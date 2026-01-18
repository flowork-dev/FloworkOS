########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\license_routes\handle_validate_license.py total lines 21 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from .base_api_route import BaseApiRoute


async def run(hub, request):
    license_manager = hub.service_instance.kernel.get_service('license_manager_service')
    if not license_manager:
        return await hub.execute_async('_json_response', {'error': 'LicenseManager service is not available.'}, status=503)
    body = await request.json()
    if 'license_key' not in body or 'machine_id' not in body:
        return await hub.execute_async('_json_response', {'error': "Request body must contain 'license_key' and 'machine_id'."}, status=400)
    (success, message) = license_manager.validate_local_license_online(body['license_key'], body['machine_id'])
    if success:
        return await hub.execute_async('_json_response', {'status': 'success', 'message': message})
    else:
        return await hub.execute_async('_json_response', {'error': message}, status=403)

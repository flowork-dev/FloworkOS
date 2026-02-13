########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\auth_routes\handle_get_profile.py total lines 22 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from .base_api_route import BaseApiRoute
from flowork_kernel.api_client import ApiClient
import re


async def run(hub, request):
    if not hub.kernel.current_user:
        hub.kernel.write_to_log('GET /auth/profile denied: User data missing in Kernel state.', 'WARN')
        return await hub.execute_async('_json_response', {'error': 'User data not found in Core cache. Session invalid.'}, status=401)
    response_data = hub.kernel.current_user.copy()
    license_manager = hub.kernel.get_service('license_manager_service')
    response_data['tier'] = hub.kernel.license_tier
    response_data['license_expires_at'] = license_manager.license_data.get('expiry_date') if license_manager and license_manager.license_data else None
    response_data['message'] = 'Profile status retrieved from Core cache.'
    hub.kernel.write_to_log('GET /auth/profile successful (Internal Cache).', 'INFO')
    return await hub.execute_async('_json_response', response_data)

########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\auth_routes\handle_logout.py total lines 15 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from .base_api_route import BaseApiRoute
from flowork_kernel.api_client import ApiClient
import re


async def run(hub, request):
    hub.service_instance.state_manager.delete('user_session_token')
    hub.kernel.current_user = None
    return await hub.execute_async('_json_response', {'message': 'Logged out successfully from Core cache.'})

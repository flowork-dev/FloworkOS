########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\auth_routes\register_routes.py total lines 12 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from flowork_kernel.api_client import ApiClient
import re


def run(hub):
    return {'POST /api/v1/auth/register': hub.handle_register, 'POST /api/v1/auth/login': hub.handle_login, 'POST /api/v1/auth/logout': hub.handle_logout, 'GET /api/v1/auth/profile': hub.handle_get_profile}

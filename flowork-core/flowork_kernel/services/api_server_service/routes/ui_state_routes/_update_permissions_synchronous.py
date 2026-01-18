########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\ui_state_routes\_update_permissions_synchronous.py total lines 19 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from .base_api_route import BaseApiRoute
import threading


def run(hub, user_data):
    license_manager = hub.kernel.get_service('license_manager_service', is_system_call=True)
    if license_manager:
        hub.execute_sync('logger', 'User data updated, re-verifying license and permissions synchronously...', 'INFO', source='ApiServer')
        license_manager.verify_license_on_startup()
        permission_manager = hub.kernel.get_service('permission_manager_service', is_system_call=True)
        if permission_manager:
            permission_manager.load_rules_from_source(license_manager.remote_permission_rules)
            hub.execute_sync('logger', 'Permissions successfully re-synced.', 'SUCCESS', source='ApiServer')

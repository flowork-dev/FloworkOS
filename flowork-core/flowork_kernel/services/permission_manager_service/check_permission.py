########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\permission_manager_service\check_permission.py total lines 16 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import logging
from flowork_kernel.services.base_service import BaseService


def run(hub, permission_name: str, context: dict=None) -> bool:
    """
        Always approve in Open Core / Dev Mode.
        Security is now handled by BaseService paths & AppRuntime sandboxing.
        """
    return True

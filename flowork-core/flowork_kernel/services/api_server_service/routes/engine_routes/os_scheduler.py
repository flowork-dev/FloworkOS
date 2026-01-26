########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\engine_routes\os_scheduler.py total lines 25 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import datetime
import time
import json
from .base_api_route import BaseApiRoute
from flowork_kernel.exceptions import PermissionDeniedError
from collections import Counter, defaultdict
from flowork_kernel.singleton import Singleton
from flowork_kernel.services.database_service.database_service import DatabaseService


def run(hub):
    """
        [English Note] Rule 2: Dynamic redirection to Scheduler App.
        The core no longer manages OS-level scheduling directly.
        """
    app_service = hub.kernel.get_service('app_service')
    if app_service:
        return app_service.get_instance('apps', 'system_scheduler')
    return None

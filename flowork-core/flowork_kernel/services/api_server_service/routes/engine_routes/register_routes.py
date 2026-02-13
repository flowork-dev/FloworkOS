########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\engine_routes\register_routes.py total lines 17 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import datetime
import time
import json
from flowork_kernel.exceptions import PermissionDeniedError
from collections import Counter, defaultdict
from flowork_kernel.singleton import Singleton
from flowork_kernel.services.database_service.database_service import DatabaseService


def run(hub):
    return {'POST /api/v1/engine/actions/schedule': hub.handle_schedule_action, 'POST /api/v1/engine/actions/cancel-schedule': hub.handle_cancel_schedule, 'GET /api/v1/engine/live-stats': hub.handle_get_live_stats}

########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\state_manager_service\handle_get_active_apps.py total lines 17 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import json
import shutil
import threading
from collections import OrderedDict


async def run(hub, request):
    user_id = request.headers.get('X-Flowork-User-ID', 'default')
    active = await hub.execute_async('get', 'active_apps', user_id=user_id, default=[])
    return {'status': 'success', 'active_apps': active}

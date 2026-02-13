########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\system_routes\register_routes.py total lines 19 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import time
import os
import shutil
import threading
import json
from collections import Counter, defaultdict
from aiohttp import web
import datetime
from flowork_kernel.exceptions import PermissionDeniedError


def run(hub) -> dict:
    return {'GET /health': hub.handle_health_check, 'GET /metrics': hub.handle_get_metrics, 'GET /api/v1/dashboard/summary': hub.handle_get_dashboard_summary, 'POST /api/v1/addons/upload': hub.handle_addon_upload, 'POST /api/v1/system/actions/hot_reload': hub.handle_hot_reload, 'GET /api/v1/status': hub.handle_get_status, 'POST /api/v1/system/actions/restart': hub.handle_system_restart, 'POST /api/v1/system/actions/shutdown': hub.handle_system_shutdown, 'POST /api/v1/system/actions/clear_cache': hub.handle_clear_cache, 'POST /api/v1/system/actions/browse_folder': hub.handle_browse_folder, 'POST /api/v1/system/diagnostics/run': hub.handle_run_diagnostics}

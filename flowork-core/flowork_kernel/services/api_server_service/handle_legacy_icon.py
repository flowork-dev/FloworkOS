########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\handle_legacy_icon.py total lines 35 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import asyncio
from aiohttp import web
import threading
import json
import uuid
import time
import os
import sys
import mimetypes
import importlib.util
import functools
from collections import deque
from flowork_kernel.utils.path_helper import get_apps_directory
from .routes.filesystem_routes import FilesystemRoutes
from .routes.engine_routes import EngineRoutes
from .routes.preset_routes import PresetRoutes
from .routes.ui_state_routes import UIStateRoutes
from flowork_kernel.utils.tracing_setup import setup_tracing


async def run(hub, request):
    app_id = request.match_info.get('app_id')
    apps_dir = get_apps_directory()
    target_dir = apps_dir / app_id
    for name in ['icon.svg', 'icon.png', 'logo.svg', 'logo.png']:
        p = target_dir / name
        if p.exists():
            return web.FileResponse(str(p), headers={'Access-Control-Allow-Origin': '*'})
    return web.Response(status=404, text='Icon not found')

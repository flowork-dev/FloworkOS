########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\handle_muscle_assets.py total lines 50 
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
    raw_filename = request.match_info.get('filename')
    filename = raw_filename.replace('assets/', '') if 'assets/' in raw_filename else raw_filename
    if not filename:
        filename = 'index.html'
    apps_dir = get_apps_directory()
    actual_path = apps_dir / app_id / filename
    if not actual_path.exists():
        actual_path = apps_dir / app_id / 'index.html'
    if str(actual_path).endswith('.html'):
        try:
            with open(actual_path, 'r', encoding='utf-8') as f:
                content = f.read()
            bridge_script = '\n                <script src="https://cdnjs.cloudflare.com/ajax/libs/ethers/6.7.0/ethers.umd.min.js"></script>\n                <script id="flowork-auth-bridge">\n                (function() {\n                    window.addEventListener(\'message\', function(e) {\n                        if (e.data && (e.data.type === \'FLOWORK_IDENTITY_SYNC\' || e.data.type === \'CMD_LOAD\')) {\n                            window.FLOWORK_AUTH = { headers: { \'X-User-Address\': e.data.userAddress, \'X-Signature\': e.data.signature, \'X-Signed-Message\': e.data.messageToSign, \'X-Flowork-Engine-ID\': e.data.engineId, \'X-Payload-Version\': \'2\' } };\n                            localStorage.setItem(\'flowork_bridge_cache\', JSON.stringify(window.FLOWORK_AUTH));\n                        }\n                    });\n                    window.FLOWORK_AUTH = JSON.parse(localStorage.getItem(\'flowork_bridge_cache\') || \'{}\');\n                    const origFetch = window.fetch;\n                    window.fetch = async function() {\n                        const args = [...arguments];\n                        if (window.FLOWORK_AUTH && window.FLOWORK_AUTH.headers && args[0].includes(\'/api/v1/\')) {\n                            if (!args[1]) args[1] = { method: \'POST\' };\n                            if (!args[1].headers) args[1].headers = {};\n                            Object.assign(args[1].headers, window.FLOWORK_AUTH.headers);\n                            if (!args[1].headers[\'Content-Type\']) args[1].headers[\'Content-Type\'] = \'application/json\';\n                        }\n                        return originalFetch.apply(this, args);\n                    };\n                })();\n                </script>\n                '
            if '</body>' in content:
                content = content.replace('</body>', bridge_script + '</body>')
            else:
                content += bridge_script
            return web.Response(body=content, content_type='text/html', headers={'Access-Control-Allow-Origin': '*'})
        except Exception:
            pass
    (ctype, _) = mimetypes.guess_type(str(actual_path))
    return web.FileResponse(actual_path, headers={'Access-Control-Allow-Origin': '*', 'Content-Type': ctype or 'application/octet-stream'})

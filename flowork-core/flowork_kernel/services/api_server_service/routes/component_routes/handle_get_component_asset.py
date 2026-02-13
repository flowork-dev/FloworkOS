########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\component_routes\handle_get_component_asset.py total lines 39 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from .base_api_route import BaseApiRoute
import os
import json
import mimetypes
import zipfile
import io
import base64
import shutil
import asyncio
from aiohttp import web
import threading


async def run(hub, request):
    """
        [MATA-MATA FIX] Serves static assets from flat folder structure.
        """
    comp_type = request.match_info.get('comp_type')
    item_id = request.match_info.get('item_id')
    filename = request.match_info.get('filename')
    app_service = hub.service_instance.kernel.get_service('app_service')
    if not app_service:
        return web.json_response({'error': 'AppService unavailable'}, status=503)
    app_info = app_service.registry['apps']['data'].get(item_id) or app_service.registry.get(comp_type, {}).get('data', {}).get(item_id)
    if not app_info:
        return web.json_response({'error': f'Component {item_id} not found'}, status=404)
    base_path = app_info.get('path')
    target_file = os.path.join(base_path, filename)
    if not os.path.exists(target_file):
        target_file = os.path.join(base_path, 'public', filename)
        if not os.path.exists(target_file):
            return web.json_response({'error': 'Asset gaib'}, status=404)
    return web.FileResponse(target_file, headers={'Access-Control-Allow-Origin': '*'})

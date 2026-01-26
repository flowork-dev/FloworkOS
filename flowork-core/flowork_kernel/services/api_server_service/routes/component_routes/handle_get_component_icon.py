########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\component_routes\handle_get_component_icon.py total lines 30 
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
    comp_type = request.match_info.get('comp_type')
    item_id = request.match_info.get('item_id')
    app_service = hub.service_instance.kernel.get_service('app_service')
    app_info = app_service.registry['apps']['data'].get(item_id) or app_service.registry.get(comp_type, {}).get('data', {}).get(item_id)
    if app_info:
        icon_filename = app_info['manifest'].get('icon_file', 'icon.svg')
        icon_path = os.path.join(app_info['path'], icon_filename)
        if os.path.exists(icon_path):
            return await (await hub.execute_async('_serve_image_file', request, icon_path))
    return await (await hub.execute_async('_serve_image_file', request, '/app/assets/default_module.png'))

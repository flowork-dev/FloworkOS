########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\component_routes\handle_get_widget_asset.py total lines 39 
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
        Serve static files from a specific widget's directory.
        """
    widget_id = request.match_info.get('widget_id')
    filename = request.match_info.get('filename')
    if not widget_id or not filename:
        return await hub.execute_async('_json_response', {'error': 'Missing widget_id or filename'}, status=400)
    (manager, error) = await hub.execute_async('_get_manager_for_type', 'widgets')
    if error:
        return await hub.execute_async('_json_response', {'error': error}, status=503)
    items = await hub.execute_async('_get_items_from_manager', manager, 'widgets')
    if widget_id not in items:
        return await hub.execute_async('_json_response', {'error': f"Widget '{widget_id}' not found."}, status=404)
    widget_data = items[widget_id]
    widget_path = widget_data.get('path') or widget_data.get('full_path')
    target_path = os.path.join(widget_path, filename)
    if not os.path.exists(target_path) or not os.path.isfile(target_path):
        return await hub.execute_async('_json_response', {'error': f"Asset '{filename}' not found."}, status=404)
    return await (await hub.execute_async('_serve_image_file', request, target_path))

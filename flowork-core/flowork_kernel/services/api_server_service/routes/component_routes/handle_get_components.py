########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\component_routes\handle_get_components.py total lines 35 
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
    resource_type = request.match_info.get('resource_type') or request.path.split('/')[3]
    item_id = request.match_info.get('item_id')
    (manager, error) = await hub.execute_async('_get_manager_for_type', resource_type)
    if error:
        return await hub.execute_async('_json_response', [], status=200)
    items = await hub.execute_async('_get_items_from_manager', manager, resource_type)
    if item_id:
        if item_id in items:
            item_data = items[item_id]
            return await hub.execute_async('_json_response', {'id': item_id, 'name': item_data['manifest'].get('name', item_id), 'manifest': item_data['manifest']})
        return await hub.execute_async('_json_response', {'error': 'Not found'}, status=404)
    response_data = []
    for (i_id, data) in items.items():
        response_data.append({'id': i_id, 'name': data['manifest'].get('name', i_id), 'icon_url': data.get('icon_url'), 'gui_url': data.get('gui_url'), 'manifest': data['manifest']})
    return await hub.execute_async('_json_response', response_data)

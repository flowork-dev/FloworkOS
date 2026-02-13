########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\component_routes\handle_app_execute_action.py total lines 54 
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
        [MATA-MATA FIX] Routes direct GUI calls to Flat App logic.
        Ensures apps like 'File Commander' can browse directories without 403.
        Fix: Menangani method handle_ui_action baik sync maupun async.
        """
    app_id = request.match_info.get('app_id')
    action = request.match_info.get('action')
    try:
        body = await request.json()
    except:
        body = {}
    app_service = hub.service_instance.kernel.get_service('app_service')
    instance = app_service.get_instance('apps', app_id)
    if not instance:
        return web.json_response({'error': f"App '{app_id}' logic failed to load."}, status=404)

    method_name = f'action_{action}'
    if hasattr(instance, method_name):
        method = getattr(instance, method_name)
        if asyncio.iscoroutinefunction(method):
            result = await method(body)
        else:
            result = method(body)
        return web.json_response(result)

    elif hasattr(instance, 'handle_ui_action'):
        possible_coro = instance.handle_ui_action(action, body)
        if asyncio.iscoroutine(possible_coro):
            result = await possible_coro
        else:
            result = possible_coro
        return web.json_response(result)

    return web.json_response({'error': f"Action '{action}' unimplemented in '{app_id}' backend."}, status=501)

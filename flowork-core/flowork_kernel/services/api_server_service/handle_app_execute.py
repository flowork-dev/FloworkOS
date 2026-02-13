########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\handle_app_execute.py total lines 83 
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
import inspect
from flowork_kernel.utils.path_helper import get_apps_directory

async def run(hub, request):
    app_id = request.match_info.get('app_id')
    action = request.match_info.get('action')
    try:
        body = await request.json()
    except:
        body = {}

    if not action: action = body.get('action')
    if not action: return web.json_response({'error': 'Action missing'}, status=400)

    if 'user_context' not in body:
        body['user_context'] = {'user_id': request.headers.get('X-Flowork-User-ID', 'system')}

    app_srv = hub.kernel.get_service('app_service')
    instance = None
    if app_srv:
        instance = app_srv.get_instance('apps', app_id) or app_srv.get_instance('tools', app_id)

    res = None
    if instance:
        handler = None
        if hasattr(instance, 'router'):
            routes = instance.router.get_routes()
            handler = routes.get(action)
        if not handler and hasattr(instance, action):
            handler = getattr(instance, action)

        if handler:
            try:
                if asyncio.iscoroutinefunction(handler):
                    res = await handler(body)
                else:
                    res = await asyncio.get_event_loop().run_in_executor(None, functools.partial(handler, body))
                if inspect.isawaitable(res): res = await res
            except Exception as e:
                return web.json_response({'error': str(e)}, status=500)

    if res is None:
        muscle = hub.kernel.get_service('app_runtime')
        if muscle:
            try:
                raw_res = muscle.execute_app(app_id=app_id, action=action, params=body, user_id=body['user_context']['user_id'])
                res = await raw_res if inspect.isawaitable(raw_res) else raw_res
                if isinstance(res, str):
                    try: res = json.loads(res)
                    except: pass
            except Exception as e:
                return web.json_response({'error': f'Muscle Failed: {str(e)}'}, status=500)

    if res is not None:
        eb = hub.kernel.get_service('event_bus')
        if eb:
            eb.publish('app.execution_completed', {
                'app_id': app_id,
                'action': action,
                'status': 'success',
                'payload_summary': str(res)[:100] # Kirim cuplikan data saja biar hemat bandwidth
            }, publisher_id=app_id)

        return web.json_response(res)

    return web.json_response({'error': f'App {app_id} not found'}, status=404)

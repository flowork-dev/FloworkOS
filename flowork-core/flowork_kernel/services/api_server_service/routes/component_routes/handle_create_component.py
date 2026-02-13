########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\component_routes\handle_create_component.py total lines 41 
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
    resource_type = request.match_info.get('resource_type')
    if resource_type == 'datasets':
        (manager, error) = await hub.execute_async('_get_manager_for_type', resource_type)
        if error:
            return await hub.execute_async('_json_response', {'error': error}, status=500)
        try:
            body = await request.json()
            name = body.get('name')
            if not name:
                return await hub.execute_async('_json_response', {'error': 'Name is required'}, status=400)
            if hasattr(manager, 'create_dataset'):
                if manager.create_dataset(name):
                    return await hub.execute_async('_json_response', {'status': 'success', 'message': f"Dataset '{name}' created."})
                return await hub.execute_async('_json_response', {'error': 'Creation failed.'}, status=409)
            dataset_app = await hub.execute_async('_get_app_instance_by_id', 'dataset_manager')
            if dataset_app and hasattr(dataset_app, 'create_dataset'):
                if dataset_app.create_dataset(name):
                    return await hub.execute_async('_json_response', {'status': 'success', 'message': f"Dataset '{name}' created via App."})
        except Exception as e:
            return await hub.execute_async('_json_response', {'error': str(e)}, status=500)
    return await hub.execute_async('_json_response', {'error': f'Create via API not supported for {resource_type}.'}, status=501)

########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\component_routes\_get_items_from_manager.py total lines 30 
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


def run(hub, manager, resource_type):
    """
        [English Note] Rule 2: Retrieving data from either the AppService registry or legacy services.
        """
    if getattr(manager, 'service_id', '') == 'app_service':
        if resource_type == 'datasets':
            return {k: v for (k, v) in manager.registry['apps']['data'].items() if v['manifest'].get('category') == 'datasets'}
        return getattr(manager, f'loaded_{resource_type}', {})
    if hasattr(manager, 'loaded_providers') and resource_type == 'ai_providers':
        return manager.loaded_providers
    return {}

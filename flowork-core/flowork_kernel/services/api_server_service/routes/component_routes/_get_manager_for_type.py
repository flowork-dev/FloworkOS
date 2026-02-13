########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\component_routes\_get_manager_for_type.py total lines 27 
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


def run(hub, resource_type):
    """[MATA-MATA FIX] Redirecting all app managers to unified AppService."""
    unified_types = ['modules', 'plugins', 'tools', 'widgets', 'triggers', 'datasets']
    if resource_type in unified_types:
        return (hub.service_instance.kernel.get_service('app_service'), None)
    manager_map = {'ai_providers': 'ai_provider_manager_service', 'models': 'ai_provider_manager_service'}
    manager = hub.service_instance.kernel.get_service(manager_map.get(resource_type))
    return (manager, None if manager else (None, 'Service unavailable'))

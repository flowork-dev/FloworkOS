########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\component_routes\__init__.py total lines 88 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from flowork_kernel.services.api_server_service.routes.base_api_route import BaseApiRoute
import importlib
import os
import logging
import asyncio
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


class ComponentRoutes(BaseApiRoute):
    def __init__(self, *args, **kwargs):
        self.cells = {}
        if not hasattr(self, 'logger'): self.logger = logging.getLogger("LazyHub")
        super().__init__(*args, **kwargs)

    def execute_sync(self, cell_name, *args, **kwargs):
        module = self._load_cell(cell_name)
        return module.run(self, *args, **kwargs)

    async def execute_async(self, cell_name, *args, **kwargs):
        module = self._load_cell(cell_name)
        return await module.run(self, *args, **kwargs)

    def _load_cell(self, cell_name):
        if cell_name not in self.cells:
            try:
                module = importlib.import_module(f".{cell_name}", package=__package__)
                self.cells[cell_name] = module
                if hasattr(self, 'logger'):
                    self.logger.info(f"[LazyHub] ✅ Loaded: {cell_name}.py")
            except Exception as e:
                if hasattr(self, 'logger'):
                    self.logger.error(f"[LazyHub] ❌ Failed to load '{cell_name}': {e}")
                raise e
        return self.cells[cell_name]

    def register_routes(self, *args, **kwargs):
        return self.execute_sync('register_routes', *args, **kwargs)
    async def handle_app_execute_action(self, *args, **kwargs):
        return await self.execute_async('handle_app_execute_action', *args, **kwargs)
    async def handle_get_component_asset(self, *args, **kwargs):
        return await self.execute_async('handle_get_component_asset', *args, **kwargs)
    async def handle_get_widget_asset(self, *args, **kwargs):
        return await self.execute_async('handle_get_widget_asset', *args, **kwargs)
    async def handle_run_component(self, *args, **kwargs):
        return await self.execute_async('handle_run_component', *args, **kwargs)
    async def handle_save_custom_component(self, *args, **kwargs):
        return await self.execute_async('handle_save_custom_component', *args, **kwargs)
    async def handle_create_component(self, *args, **kwargs):
        return await self.execute_async('handle_create_component', *args, **kwargs)
    def _get_app_instance_by_id(self, *args, **kwargs):
        return self.execute_sync('_get_app_instance_by_id', *args, **kwargs)
    async def handle_package_component(self, *args, **kwargs):
        return await self.execute_async('handle_package_component', *args, **kwargs)
    async def handle_install_package(self, *args, **kwargs):
        return await self.execute_async('handle_install_package', *args, **kwargs)
    async def _serve_image_file(self, *args, **kwargs):
        return await self.execute_async('_serve_image_file', *args, **kwargs)
    async def handle_get_component_icon(self, *args, **kwargs):
        return await self.execute_async('handle_get_component_icon', *args, **kwargs)
    async def handle_get_ai_provider_services(self, *args, **kwargs):
        return await self.execute_async('handle_get_ai_provider_services', *args, **kwargs)
    def _get_manager_for_type(self, *args, **kwargs):
        return self.execute_sync('_get_manager_for_type', *args, **kwargs)
    def _get_items_from_manager(self, *args, **kwargs):
        return self.execute_sync('_get_items_from_manager', *args, **kwargs)
    async def handle_get_components(self, *args, **kwargs):
        return await self.execute_async('handle_get_components', *args, **kwargs)
    async def handle_install_components(self, *args, **kwargs):
        return await self.execute_async('handle_install_components', *args, **kwargs)
    async def handle_delete_components(self, *args, **kwargs):
        return await self.execute_async('handle_delete_components', *args, **kwargs)
    async def handle_patch_component_state(self, *args, **kwargs):
        return await self.execute_async('handle_patch_component_state', *args, **kwargs)

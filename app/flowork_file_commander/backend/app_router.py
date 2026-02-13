########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\flowork_file_commander\backend\app_router.py total lines 115 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import asyncio
from aiohttp import web
import os
import sys
import importlib.util
import logging

backend_path = os.path.dirname(os.path.abspath(__file__))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

try:
    service_path = os.path.join(backend_path, "app_service.py")
    spec = importlib.util.spec_from_file_location("fc_service_module", service_path)
    fc_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fc_module)
    FileManagerService = fc_module.FileManagerService
except Exception as e:
    try:
        from app_service import FileManagerService
    except ImportError:
        print(f"❌ [FileCommander] Service import failed: {e}")
        raise e

class AppRouter:
    def __init__(self, service):
        self.service = service
        self.logger = logging.getLogger("AppRouter.FileCommander")
        self.logger.info("🔗 [AppRouter] File Commander Router Online (Async Hybrid Mode).")

    def get_routes(self):
        """[English Note] Explicit route mapping for GUI index.html actions."""
        return {
            "browse": self.browse_handler,
            "create": self.create_handler,
            "create_folder": self.create_handler,
            "create_file": self.create_file_handler,
            "delete": self.delete_handler,
            "rename": self.rename_handler,
            "read_file": self.read_handler,
            "download_file": self.download_handler,
            "batch_delete": self.batch_delete_handler
        }

    def _get_user_id(self, payload):
        uid = payload.get("user_context", {}).get("user_id")
        if not uid: uid = payload.get("user_id")
        if not uid: uid = "system"
        return uid

    async def browse_handler(self, payload: dict):
        path = payload.get("path")
        user_id = self._get_user_id(payload)
        return await self.service.list_files(path, user_id)

    async def create_handler(self, payload: dict):
        path = payload.get("path")
        name = payload.get("name")
        user_id = self._get_user_id(payload)

        if not name: return {"status": "error", "error": "Folder name required"}

        return await self.service.create_new_folder(path, name, user_id)

    async def create_file_handler(self, payload: dict):
        path = payload.get("path")
        name = payload.get("name")
        content = payload.get("content", "")
        user_id = self._get_user_id(payload)

        if not name: return {"status": "error", "error": "File name required"}

        return await self.service.create_new_file(path, name, content, user_id)

    async def delete_handler(self, payload: dict):
        path = payload.get("path")
        user_id = self._get_user_id(payload)
        return await self.service.delete_item(path, user_id)

    async def batch_delete_handler(self, payload: dict):
        paths = payload.get("paths", [])
        user_id = self._get_user_id(payload)
        return await self.service.delete_batch_items(paths, user_id)

    async def rename_handler(self, payload: dict):
        path = payload.get("path")
        new_name = payload.get("new_name")
        user_id = self._get_user_id(payload)

        if not new_name: return {"status": "error", "error": "New name required"}

        return await self.service.rename_item(path, new_name, user_id)

    async def read_handler(self, payload: dict):
        path = payload.get("path")
        user_id = self._get_user_id(payload)
        return await self.service.read_file_content(path, user_id)

    async def download_handler(self, payload: dict):
        path = payload.get("path")
        user_id = self._get_user_id(payload)
        real_path = await self.service.get_download_path(path, user_id)

        if real_path and os.path.exists(real_path):
            filename = os.path.basename(real_path)
            return web.FileResponse(real_path, headers={
                "Content-Disposition": f"attachment; filename=\"{filename}\""
            })
        return web.Response(text="File not found", status=404)

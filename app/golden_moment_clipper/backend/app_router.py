########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\golden_moment_clipper\backend\app_router.py total lines 67 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import asyncio
import threading
from aiohttp import web
import os
import sys
import logging

backend_path = os.path.dirname(os.path.abspath(__file__))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app_service import GoldenMomentService

class AppRouter:
    def __init__(self, service_instance):
        self.service = service_instance
        self.logger = logging.getLogger("AppRouter.GoldenMoment")
        self.logger.info("🔗 [AppRouter] Golden Moment Router Online.")

    def get_routes(self):
        return {
            "start_processing": self.start_processing,
            "progress": self.progress_check,
            "browse_directory": self.browse_handler,
            "status": self.status_handler
        }

    def _get_user_id(self, payload):
        uid = payload.get("user_id")
        if not uid: uid = payload.get("user_context", {}).get("user_id")
        if not uid: uid = "system"
        return uid

    async def browse_handler(self, payload: dict):
        path = payload.get("path")
        user_id = self._get_user_id(payload)
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.service.list_directory, path, user_id)

    async def start_processing(self, payload: dict):
        user_id = self._get_user_id(payload)

        if not payload.get("input_folder_path") or not payload.get("output_folder"):
            return {"status": "error", "error": "Missing input/output folder"}

        job_id = self.service.init_job(user_id)

        t = threading.Thread(
            target=self.service.run_process_safe,
            args=(job_id, payload, user_id),
            daemon=True
        )
        t.start()
        return {"status": "success", "job_id": job_id}

    async def progress_check(self, payload: dict):
        job_id = payload.get("job_id")
        return self.service.get_job_status(job_id)

    async def status_handler(self, payload: dict):
        return {"status": "online", "mode": "muscle_bridge"}

########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\neural_dojo\backend\app_router.py total lines 41 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import logging
import asyncio

class AppRouter:
    def __init__(self, service_instance):
        self.service = service_instance
        self.logger = logging.getLogger("AppRouter.NeuralDojo")

    def get_routes(self):
        return {
            "start_training": self.handle_start,
            "stop_training": self.handle_stop,
            "get_status": self.handle_status,
            "get_local_models": self.handle_get_models,
            "browse_directory": self.handle_browse
        }

    async def handle_start(self, payload: dict):
        config = payload.get("config", {})
        return self.service.start_training(config)

    async def handle_stop(self, payload: dict):
        return self.service.stop_training()

    async def handle_status(self, payload: dict):
        return self.service.get_status()

    async def handle_get_models(self, payload: dict):
        return self.service.scan_local_models()

    async def handle_browse(self, payload: dict):
        loop = asyncio.get_event_loop()
        path = payload.get("path", "")
        user_id = payload.get("user_id", "system")
        return await loop.run_in_executor(None, self.service.list_directory, path, user_id)

########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\flowork_architect\backend\app_router.py total lines 81 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import sys
import logging
import traceback
import importlib.util

backend_path = os.path.dirname(os.path.abspath(__file__))

class AppRouter:
    def __init__(self, app_context):
        self.logger = logging.getLogger("AppRouter.Architect")

        try:
            service_file = os.path.join(backend_path, "app_service.py")
            module_name = "flowork_architect.backend.app_service"

            spec = importlib.util.spec_from_file_location(module_name, service_file)
            service_mod = importlib.util.module_from_spec(spec)

            sys.modules[module_name] = service_mod
            spec.loader.exec_module(service_mod)

            ArchitectService = service_mod.ArchitectService

            real_kernel = getattr(app_context, 'kernel', app_context)
            self.service = ArchitectService(real_kernel, "flowork_architect_service")
            self.logger.info("🔗 [AppRouter] Cortex Router Linked Successfully (Unique Import).")

        except Exception as e:
            self.logger.error(f"🔥 CRITICAL IMPORT ERROR: {e}\n{traceback.format_exc()}")
            raise e

    def get_routes(self):
        return {
            "scan": self.run_scan,
            "force_sync": self.force_sync,
            "get_intel": self.get_intel,
            "export_atlas": self.export_atlas,
            "export_json": self.export_json,
            "save_file": self.save_file,
            "crud": self.crud_action
        }


    async def run_scan(self, payload):
        try:
            data = self.service.run_scan()
            return {"status": "success", "data": data}
        except Exception as e:
            self.logger.error(f"Scan Handler Error: {e}")
            return {"status": "error", "message": str(e), "data": {"nodes":[], "edges":[], "zombie_count":0}}

    async def force_sync(self, payload):
        try: return self.service.force_sync()
        except Exception as e: return {"status": "error", "message": str(e)}

    async def get_intel(self, payload):
        try: return self.service.get_file_intel(payload.get("path"))
        except Exception as e: return {"status": "error", "message": str(e)}

    async def export_atlas(self, payload):
        try: return self.service.export_atlas()
        except Exception as e: return {"status": "error", "message": str(e)}

    async def export_json(self, payload):
        try: return self.service.export_json_atlas()
        except Exception as e: return {"status": "error", "message": str(e)}

    async def save_file(self, payload):
        try: return self.service.save_file(payload.get("path"), payload.get("content"))
        except Exception as e: return {"status": "error", "message": str(e)}

    async def crud_action(self, payload):
        try: return self.service.handle_crud(payload)
        except Exception as e: return {"status": "error", "message": str(e)}

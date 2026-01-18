########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\universal_downloader\backend\node.py total lines 134 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import logging
import os
import asyncio
import json
import time
import importlib.util
from flowork_kernel.flow_sdk.base_app_node import BaseAppNode

try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    service_path = os.path.join(current_dir, "app_service.py")

    spec = importlib.util.spec_from_file_location("ud_node_service_module", service_path)
    ud_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ud_module)
    UniversalDownloaderService = ud_module.UniversalDownloaderService
except Exception as e:
    logging.getLogger("ImportFallback").warning(f"⚠️ Falling back to standard import due to: {e}")
    from app_service import UniversalDownloaderService

class DownloaderNode(BaseAppNode):
    def __init__(self, node_id, properties, kernel):
        super().__init__(node_id, properties, kernel)
        self.logger = logging.getLogger(f"Node.Downloader.{node_id}")
        self.service = UniversalDownloaderService(kernel, f"downloader_svc_{node_id}")
        self.is_standalone = True

    def update_status(self, message, status="RUNNING"):
        """
        Lapor status ke EventBus agar UI Canvas tau progress-nya.
        """
        self.logger.info(f"[{status}] {message}")

        if hasattr(self, 'event_bus') and self.event_bus:
            try:
                user_id = self.context.get("user_context", {}).get("user_id", "system")

                execution_id = self.context.get("execution_id")
                job_id = self.context.get("job_id")

                payload = {
                    "execution_id": execution_id, # <--- INI KUNCI UI CANVAS
                    "job_id": job_id,
                    "node_id": self.node_id,
                    "status": status,
                    "message": message,
                    "timestamp": time.time(),
                    "_target_user_id": user_id
                }

                self.event_bus.publish("WORKFLOW_EXECUTION_UPDATE", payload)

                if status in ["COMPLETED", "FAILED"]:
                     self.event_bus.publish("NODE_EXECUTION_FINISHED", payload)

            except Exception as e:
                self.logger.warning(f"Failed to emit status update: {e}")

    async def execute(self, inputs):
        """
        Main Execution Logic for Workflow Node
        """
        self.update_status("🚀 Initializing Downloader Node...", "RUNNING")

        target_url = inputs.get("url", "")
        format_mode = inputs.get("format_mode", "best")
        out_raw = inputs.get("output_folder") or inputs.get("output_dir") or ""

        job_id = self.context.get("job_id", "adhoc_task")
        user_context = self.context.get("user_context", {})
        user_id = user_context.get("user_id", "system")

        if not target_url:
            return {"error": "No URL provided"}

        try:
            self.logger.info(f"🚀 [Direct-Link] Starting Download Synchronously: {target_url}")

            loop = asyncio.get_running_loop()

            if hasattr(self.service, '_perform_download'):
                 result = await loop.run_in_executor(
                    None,
                    self.service._perform_download,
                    target_url,
                    out_raw,
                    format_mode,
                    user_id,
                    job_id # Pass job_id explicitly if supported
                 )
            else:
                 self.logger.warning("⚠️ Internal method '_perform_download' not found. Trying 'run_download'...")
                 result = await loop.run_in_executor(
                    None,
                    self.service.run_download,
                    target_url,
                    out_raw,
                    format_mode,
                    user_id
                 )

            downloaded = result.get('downloaded', [])
            count = len(downloaded)

            if result and result.get("status") == "success" and count > 0:
                self.logger.info(f"🎉 [Direct-Link] Download Complete! Files: {count}")

                self.update_status(f"✅ Downloaded {count} files.", "COMPLETED")

                return {
                    "success": {
                        "status": "success",
                        "data": result,
                        "message": "Download finished successfully"
                    }
                }
            else:
                error_msg = result.get("error") if result else "Unknown Error"
                if count == 0 and not error_msg:
                    error_msg = "Download returned 0 files. Check Youtube Auth/Cookies."

                self.update_status(f"❌ Failed: {error_msg}", "FAILED")
                return {"error": f"Download Failed: {error_msg}"}

        except Exception as e:
            self.logger.error(f"❌ [Direct Execution Failure]: {str(e)}")
            self.update_status(f"❌ Critical Error: {str(e)}", "FAILED")
            return {"error": f"Critical Node Error: {str(e)}"}

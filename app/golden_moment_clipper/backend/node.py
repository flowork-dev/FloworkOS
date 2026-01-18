########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\golden_moment_clipper\backend\node.py total lines 66 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import uuid
import logging
import asyncio
from flowork_kernel.flow_sdk.base_app_node import BaseAppNode
from app_service import GoldenMomentService

class GoldenClipperNode(BaseAppNode):
    def __init__(self, node_id, properties, kernel):
        super().__init__(node_id, properties, kernel)
        self.logger = logging.getLogger(f"App.Node.{node_id}")

        self.service = GoldenMomentService(kernel, f"golden_svc_{node_id}")

        self.muscle = kernel.get_service("app_runtime")
        self.logger.info(f"✅ GoldenClipperNode {node_id} initialized (Hybrid Mode).")

    async def execute(self, inputs):
        self.update_status("🎬 Initializing AI Processor...", "RUNNING")

        job_id = self.context.get("job_id", f"node_{uuid.uuid4().hex[:8]}")
        user_id = self.context.get("user_id", "system") # Default system, service will auto-detect

        config = {
            "input_folder_path": inputs.get("input_folder_path") or self.properties.get("input_folder_path", ""),
            "output_folder": inputs.get("output_folder") or self.properties.get("output_folder", ""),
            "timestamps": inputs.get("timestamps") or self.properties.get("timestamps", ""),
            "outro_path": inputs.get("outro_path") or self.properties.get("outro_path", ""),
            "whisper_model": inputs.get("whisper_model") or self.properties.get("whisper_model", "small"),
            "resize_mode": inputs.get("resize_mode") or self.properties.get("resize_mode", "podcast_split"),
            "smart_cut_mode": inputs.get("smart_cut_mode") or self.properties.get("smart_cut_mode", True),
            "remove_silence": inputs.get("remove_silence") or self.properties.get("remove_silence", False),
            "add_subtitles": inputs.get("add_subtitles") or self.properties.get("add_subtitles", True),
            "watermark_text": inputs.get("watermark_text") or self.properties.get("watermark_text", "Created with Flowork"),
            "merge_clips": inputs.get("merge_clips") or self.properties.get("merge_clips", False)
        }

        self.logger.info(f"🚀 [Node] Starting Video Process (Job: {job_id})")

        try:
            self.service.active_jobs[job_id] = {"status": "running", "logs": [], "user_id": user_id}

            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self.service.run_process_safe, job_id, config, user_id)

            final_status = self.service.active_jobs[job_id].get("status", "unknown")

            if final_status == "completed":
                self.logger.info(f"✅ Batch Process Finished Successfully.")
                return self.success({
                    "status": "success",
                    "job_id": job_id,
                    "message": "Video processing completed."
                })
            else:
                return self.error(f"Processing failed. Status: {final_status}")

        except Exception as e:
            self.logger.error(f"🔥 Node Execution Failed: {e}")
            return self.error(str(e))

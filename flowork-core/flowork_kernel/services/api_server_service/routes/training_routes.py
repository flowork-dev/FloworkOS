########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\training_routes.py total lines 158 
########################################################################

from .base_api_route import BaseApiRoute
import asyncio
import traceback
import os

class TrainingRoutes(BaseApiRoute):

    def register_routes(self):
        return {
            "POST /api/v1/training/start": self.handle_start_training_job,
            "POST /api/v1/training/upload": self.handle_upload_dataset,
            "POST /api/v1/training/convert": self.handle_start_conversion_job,
            "POST /api/v1/training/sparring": self.handle_sparring_match,
            "GET /api/v1/training/status/{job_id}": self.handle_get_training_job_status,
            "GET /api/v1/training/jobs": self.handle_list_jobs,
            "DELETE /api/v1/training/jobs/{job_id}": self.handle_delete_job,
        }

    async def handle_start_training_job(self, request):
        try:
            training_service = self.service_instance.training_service
            if not training_service:
                return self._json_response({"error": "Service unavailable"}, status=503)

            body = await request.json()
            if not body: return self._json_response({"error": "Body required"}, status=400)

            result = training_service.start_fine_tuning_job(
                body.get("base_model_id"),
                body.get("dataset_name"),
                body.get("new_model_name"),
                body.get("training_args", {})
            )

            if "error" in result: return self._json_response(result, status=400)
            return self._json_response(result, status=202)
        except Exception as e:
            traceback.print_exc()
            return self._json_response({"error": str(e)}, status=500)

    async def handle_upload_dataset(self, request):
        """
        Handle Single File, Multiple Files, or ZIP uploads for training.
        """
        try:
            training_service = self.service_instance.training_service
            if not training_service: return self._json_response({"error": "Service unavailable"}, status=503)

            content_type = request.headers.get("Content-Type", "")
            if "multipart" not in content_type.lower():
                return self._json_response({
                    "error": f"Invalid Content-Type. Expected multipart/form-data, got '{content_type}'"
                }, status=400)

            reader = await request.multipart()

            upload_session_files = []

            print("[Upload] Starting multipart stream reading...", flush=True)

            while True:
                field = await reader.next()
                if not field: break

                if field.name == 'file':
                    filename = field.filename
                    if not filename: continue

                    file_content = await field.read()

                    size_kb = len(file_content) / 1024
                    print(f"[Upload] Received: {filename} ({size_kb:.2f} KB)", flush=True)

                    upload_session_files.append({
                        "filename": filename,
                        "content": file_content
                    })

            if not upload_session_files:
                return self._json_response({"error": "No valid files received in payload"}, status=400)

            saved_dataset_name = training_service.handle_bulk_upload(upload_session_files)

            return self._json_response({"success": True, "filename": saved_dataset_name})

        except Exception as e:
            print(f"[Upload Error] {str(e)}")
            traceback.print_exc()
            return self._json_response({"error": f"Upload Failed: {str(e)}"}, status=500)

    async def handle_start_conversion_job(self, request):
        training_service = self.service_instance.training_service
        if not training_service:
            return self._json_response({"error": "Service unavailable"}, status=503)

        body = await request.json()
        if not body: return self._json_response({"error": "Body required"}, status=400)

        result = training_service.start_conversion_job(
            body.get("model_id"),
            body.get("quantization", "q4_k_m"),
            body.get("new_model_name"),
            body.get("mode", "gguf"),
            body.get("strategy", "auto")
        )

        if "error" in result: return self._json_response(result, status=400)
        return self._json_response(result, status=202)

    async def handle_sparring_match(self, request):
        training_service = self.service_instance.training_service
        if not training_service: return self._json_response({"error": "Service unavailable"}, status=503)

        body = await request.json()

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,
            lambda: training_service.run_sparring_match(
                body.get("base_model_id"),
                body.get("adapter_model_id"),
                body.get("prompt")
            )
        )

        if "error" in result: return self._json_response(result, status=500)
        return self._json_response(result)

    async def handle_get_training_job_status(self, request):
        job_id = request.match_info.get("job_id")
        training_service = self.service_instance.training_service
        if not training_service: return self._json_response({"error": "Service unavailable"}, status=503)

        status = training_service.get_job_status(job_id)
        return self._json_response(status)

    async def handle_list_jobs(self, request):
        training_service = self.service_instance.training_service
        if not training_service: return self._json_response({"error": "Service unavailable"}, status=503)

        jobs = training_service.list_training_jobs()
        return self._json_response(jobs)

    async def handle_delete_job(self, request):
        job_id = request.match_info.get("job_id")
        training_service = self.service_instance.training_service
        if not training_service: return self._json_response({"error": "Service unavailable"}, status=503)

        success = training_service.delete_job(job_id)
        if success:
            return self._json_response({"status": "deleted"})
        return self._json_response({"error": "Job not found"}, status=404)

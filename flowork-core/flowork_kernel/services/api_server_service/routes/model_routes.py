########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\model_routes.py total lines 259 
########################################################################

from .base_api_route import BaseApiRoute
from aiohttp import web
import types
import os

class ModelRoutes(BaseApiRoute):

    def register_routes(self):
        return {
            "POST /api/v1/models/convert": self.handle_post_model_conversion,
            "GET /api/v1/models/convert/status/{job_id}": self.handle_get_conversion_status,
            "POST /api/v1/models/upload": self.handle_model_upload,

            "GET /api/v1/ai_models": self.handle_get_all_ai_models,
            "GET /api/v1/ai/models": self.handle_get_all_ai_models,

            "GET /api/v1/models/local": self.handle_get_local_models,

            "POST /api/v1/models/requantize": self.handle_post_model_requantize,

            "POST /api/v1/ai/playground": self.handle_ai_playground,

            "POST /api/v1/ai/chat/completions": self.handle_ai_playground,
        }

    async def handle_get_local_models(self, request):
        """
        [NEW] Khusus mengambil list model lokal untuk keperluan Fine-Tuning.
        Endpoint ini dipanggil oleh AI Trainer (GUI).
        """
        ai_manager = self.service_instance.ai_provider_manager_service
        if not ai_manager:
            return self._json_response(
                {"error": "AIProviderManagerService is not available."}, status=503
            )

        try:
            local_models = []
            if hasattr(ai_manager, 'local_models'):
                for mid, m in ai_manager.local_models.items():
                    raw_name = m.get('name', 'Unknown')
                    display_name = raw_name.replace('_', ' ').replace('-', ' ').title() if raw_name else "Unknown Model"

                    local_models.append({
                        "id": mid,
                        "name": display_name,
                        "raw_name": raw_name,
                        "version": "Local",
                        "tier": "free",
                        "type": "local_model",
                        "category": m.get('category', 'unknown'),
                        "full_path": m.get('full_path')
                    })

            self.logger(f"Serving {len(local_models)} local models to client.", "INFO")
            return self._json_response(local_models)
        except Exception as e:
            self.logger(f"Error listing local AI models: {e}", "ERROR")
            return self._json_response(
                {"error": f"Could not list local AI models: {e}"}, status=500
            )

    async def handle_ai_playground(self, request):
        """
        [NEW] Handle AI Interaction.
        Supports:
        1. Contextual Memory ('messages' list)
        2. Real-time Streaming ('stream' boolean)
        """
        ai_manager = self.service_instance.ai_provider_manager_service
        if not ai_manager:
            return self._json_response(
                {"error": "AI Service unavailable."}, status=503
            )

        try:
            body = await request.json()

            endpoint_id = body.get("endpoint_id") or body.get("model")

            prompt = body.get("prompt")
            task_type = body.get("task_type", "general")
            messages = body.get("messages", [])

            stream_requested = body.get("stream", False)

            if not prompt and messages:
                last_msg = messages[-1]
                if last_msg.get('role') == 'user':
                    prompt = last_msg.get('content')

            if not prompt or not endpoint_id:
                return self._json_response(
                    {"error": "Missing 'prompt' (or messages) or 'endpoint_id' (model)."}, status=400
                )

            self.logger(f"[AI Request] Model: {endpoint_id} | Stream: {stream_requested}", "INFO")

            result = ai_manager.query_ai_by_task(
                task_type=task_type,
                prompt=prompt,
                endpoint_id=endpoint_id,
                messages=messages,
                stream=stream_requested
            )

            if isinstance(result, types.GeneratorType):
                response = web.StreamResponse(
                    status=200,
                    reason='OK',
                    headers={
                        'Content-Type': 'text/plain',
                        'Cache-Control': 'no-cache',
                        'Connection': 'keep-alive'
                    }
                )
                await response.prepare(request)

                try:
                    for chunk in result:
                        if chunk:
                            await response.write(str(chunk).encode('utf-8'))

                    await response.write_eof()
                    return response

                except Exception as stream_err:
                    self.logger(f"[Streaming Error] {stream_err}", "ERROR")
                    return response

            elif isinstance(result, dict):
                if "error" in result:
                    return self._json_response(result, status=500)
                return self._json_response(result)

            else:
                return self._json_response({"error": "Unknown response type from AI Engine"}, status=500)

        except Exception as e:
            self.logger(f"[Playground] Critical Error: {e}", "ERROR")
            return self._json_response({"error": str(e)}, status=500)

    async def handle_post_model_requantize(self, request):
        converter_service = self.service_instance.converter_service
        if not converter_service:
            return self._json_response(
                {
                    "error": "ModelConverterService is not available due to license restrictions."
                },
                status=503,
            )
        body = await request.json()
        required_keys = ["source_gguf_path", "output_gguf_name"]
        if not all(key in body for key in required_keys):
            return self._json_response(
                {"error": f"Request body must contain: {', '.join(required_keys)}"},
                status=400,
            )
        result = converter_service.start_requantize_job(
            body["source_gguf_path"],
            body["output_gguf_name"],
            body.get("quantize_method", "Q4_K_M"),
        )
        if "error" in result:
            return self._json_response(result, status=409)
        else:
            return self._json_response(result, status=202)

    async def handle_post_model_conversion(self, request):
        converter_service = self.service_instance.converter_service
        if not converter_service:
            return self._json_response(
                {
                    "error": "ModelConverterService is not available due to license restrictions."
                },
                status=503,
            )
        body = await request.json()
        required_keys = ["source_model_folder", "output_gguf_name"]
        if not all(key in body for key in required_keys):
            return self._json_response(
                {"error": f"Request body must contain: {', '.join(required_keys)}"},
                status=400,
            )
        result = converter_service.start_conversion_job(
            body["source_model_folder"],
            body["output_gguf_name"],
            body.get("quantize_method", "Q4_K_M"),
        )
        if "error" in result:
            return self._json_response(result, status=409)
        else:
            return self._json_response(result, status=202)

    async def handle_get_conversion_status(self, request):
        job_id = request.match_info.get("job_id")
        converter_service = self.service_instance.converter_service
        if not converter_service:
            return self._json_response(
                {
                    "error": "ModelConverterService is not available due to license restrictions."
                },
                status=503,
            )
        status = converter_service.get_job_status(job_id)
        if "error" in status:
            return self._json_response(status, status=404)
        else:
            return self._json_response(status)

    async def handle_model_upload(self, request):
        return self._json_response(
            {"error": "Not implemented for aiohttp yet."}, status=501
        )

    async def handle_get_all_ai_models(self, request):
        """
        Mengambil SEMUA model baik Provider (OpenAI/Gemini) maupun Local.
        """
        ai_manager = self.service_instance.ai_provider_manager_service
        if not ai_manager:
            return self._json_response(
                {"error": "AIProviderManagerService is not available."}, status=503
            )

        try:
            if hasattr(ai_manager, 'get_loaded_providers_info'):
                all_models = ai_manager.get_loaded_providers_info()
            else:
                all_models = []
                if hasattr(ai_manager, 'loaded_providers'):
                    for pid, p in ai_manager.loaded_providers.items():
                        man = p.get_manifest() if hasattr(p, 'get_manifest') else {}
                        all_models.append({
                            "id": pid, "name": man.get('name', pid),
                            "version": man.get('version', '1.0'), "tier": getattr(p, 'TIER', 'free').lower(),
                            "type": "provider"
                        })
                if hasattr(ai_manager, 'local_models'):
                    for mid, m in ai_manager.local_models.items():
                        all_models.append({
                            "id": mid, "name": m.get('name', 'Unknown'),
                            "version": "Local",
                            "tier": "free", "type": "local_model", "category": m.get('category', 'unknown')
                        })

            return self._json_response(all_models)

        except Exception as e:
            self.logger(f"Error listing AI models: {e}", "ERROR")
            return self._json_response(
                {"error": f"Could not list AI models: {e}"}, status=500
            )

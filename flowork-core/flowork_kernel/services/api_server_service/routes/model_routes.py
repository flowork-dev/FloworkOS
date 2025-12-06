########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\model_routes.py total lines 388 
########################################################################

from .base_api_route import BaseApiRoute
from aiohttp import web
import types
import json
import asyncio
import random
import concurrent.futures
import time

class ModelRoutes(BaseApiRoute):

    LOADING_MESSAGES = [
        "Aligning neural pathways...",
        "Parsing context vectors...",
        "Calibrating attention heads...",
        "Synthesizing cognitive patterns...",
        "Loading knowledge graph...",
        "Optimizing tensor operations...",
        "Establishing semantic connections...",
        "Thinking deeply...",
        "Analyzing prompt intent...",
        "Generating creative matrix...",
        "Consulting the digital oracle...",
        "Warming up the GPU cores...",
        "De-quantizing model weights...",
        "Tracing diffusion paths...",
        "Applying latent transformations...",
        "Refining output tensors..."
    ]

    def register_routes(self):
        return {
            "GET /api/v1/ai_models": self.handle_get_all_ai_models,
            "GET /api/v1/ai/models": self.handle_get_all_ai_models,
            "GET /api/v1/models/local": self.handle_get_local_models,
            "POST /api/v1/ai/playground": self.handle_ai_playground,
            "POST /api/v1/ai/chat/completions": self.handle_ai_playground,

            "POST /api/v1/ai/sessions": self.handle_create_session,
            "GET /api/v1/ai/sessions": self.handle_list_sessions,
            "GET /api/v1/ai/sessions/{id}": self.handle_get_session,
            "PATCH /api/v1/ai/sessions/{id}": self.handle_update_session,
            "DELETE /api/v1/ai/sessions/{id}": self.handle_delete_session,

            "POST /api/v1/ai/jobs/submit": self.handle_submit_job,
            "GET /api/v1/ai/jobs/{id}": self.handle_get_job_status,

            "GET /api/v1/models/conversions": self.handle_get_conversion_status,
            "POST /api/v1/models/convert": self.handle_post_model_conversion, # [FIXED] Updated route name match
            "POST /api/v1/models/upload": self.handle_model_upload,
            "POST /api/v1/models/requantize": self.handle_post_model_requantize,
        }

    def _get_user_id(self, request):
        """
        Extracts User ID safely to prevent Data Leakage between users.
        """
        user_context = getattr(request, "user_context", None) or request.get("user_context", {})
        user_id = user_context.get("user_id") or user_context.get("id") or "public_guest"
        return str(user_id)

    async def handle_create_session(self, request):
        ai_manager = self.service_instance.ai_provider_manager_service
        if not ai_manager: return self._json_response({"error": "AI Service unavailable."}, status=503)

        try:
            body = await request.json()
            user_id = self._get_user_id(request)

            session = ai_manager.create_session(
                title=body.get("title", "New Chat"),
                model_id=body.get("model_id")
            )

            session['user_id'] = user_id
            ai_manager.save_session(session['id'], session)

            return self._json_response(session)
        except Exception as e:
            return self._json_response({"error": str(e)}, status=500)

    async def handle_list_sessions(self, request):
        ai_manager = self.service_instance.ai_provider_manager_service
        if not ai_manager: return self._json_response({"error": "AI Service unavailable."}, status=503)

        user_id = self._get_user_id(request)
        all_sessions = ai_manager.list_sessions()

        my_sessions = [s for s in all_sessions if s.get('user_id') == user_id]

        return self._json_response(my_sessions)

    async def handle_get_session(self, request):
        ai_manager = self.service_instance.ai_provider_manager_service
        session_id = request.match_info['id']
        user_id = self._get_user_id(request)

        session = ai_manager.get_session(session_id)

        if not session:
            return self._json_response({"error": "Session not found"}, status=404)


        return self._json_response(session)

    async def handle_update_session(self, request):
        ai_manager = self.service_instance.ai_provider_manager_service
        session_id = request.match_info['id']
        user_id = self._get_user_id(request)

        session = ai_manager.get_session(session_id)
        if not session:
            return self._json_response({"error": "Session not found"}, status=404)

        try:
            body = await request.json()

            if 'title' in body: session['title'] = body['title']
            if 'messages' in body: session['messages'] = body['messages']
            if 'modelId' in body: session['modelId'] = body['modelId']

            ai_manager.save_session(session_id, session)
            return self._json_response(session)
        except Exception as e:
            return self._json_response({"error": str(e)}, status=500)

    async def handle_delete_session(self, request):
        ai_manager = self.service_instance.ai_provider_manager_service
        session_id = request.match_info['id']
        user_id = self._get_user_id(request)

        session = ai_manager.get_session(session_id)
        if not session: return self._json_response({"status": "ignored"})


        ai_manager.delete_session(session_id)
        return self._json_response({"status": "deleted"})

    async def handle_submit_job(self, request):
        ai_manager = self.service_instance.ai_provider_manager_service
        if not ai_manager: return self._json_response({"error": "AI Service unavailable."}, status=503)

        try:
            body = await request.json()
            user_id = self._get_user_id(request)

            task_type = body.get('type', 'generation') # generation, training, etc.
            payload = body.get('payload', {})

            session_id = payload.get('session_id')
            if session_id:
                sess = ai_manager.get_session(session_id)
                if not sess:
                    return self._json_response({"error": "Invalid Session ID"}, status=400)

            payload['user_id'] = user_id

            job = await ai_manager.submit_job(task_type, payload)

            return self._json_response({
                "status": "queued",
                "job_id": job['id'],
                "position": job['position'],
                "message": f"Job submitted. Position in queue: {job['position']}"
            })

        except Exception as e:
            self.logger(f"[Job Submit Error] {e}", "ERROR")
            return self._json_response({"error": str(e)}, status=500)

    async def handle_get_job_status(self, request):
        ai_manager = self.service_instance.ai_provider_manager_service
        job_id = request.match_info['id']
        user_id = self._get_user_id(request)

        if job_id in ai_manager.active_jobs:
            job = ai_manager.active_jobs[job_id]

            job_owner = job.get('payload', {}).get('user_id')
            if job_owner and job_owner != user_id:
                return self._json_response({"error": "Unauthorized"}, status=403)

            current_pos = 0
            if job['status'] == 'QUEUED':
                current_pos = job['position']

            response = {
                "id": job['id'],
                "status": job['status'],
                "created_at": job['submitted_at'],
                "position": current_pos
            }

            if job['status'] == 'COMPLETED':
                response['result'] = job.get('result')
            elif job['status'] == 'FAILED':
                response['error'] = job.get('error')

            return self._json_response(response)

        return self._json_response({"error": "Job not found or expired"}, status=404)

    async def handle_get_local_models(self, request):
        ai_manager = self.service_instance.ai_provider_manager_service
        if not ai_manager: return self._json_response({"error": "AI Service unavailable."}, status=503)
        return self._json_response(ai_manager.get_loaded_providers_info())

    async def handle_get_all_ai_models(self, request):
        return await self.handle_get_local_models(request)

    async def handle_ai_playground(self, request):
        ai_manager = self.service_instance.ai_provider_manager_service
        if not ai_manager: return self._json_response({"error": "AI Service unavailable."}, status=503)

        try:
            body = await request.json()
            endpoint_id = body.get("endpoint_id") or body.get("model")
            prompt = body.get("prompt")
            messages = body.get("messages", [])
            stream_requested = body.get("stream", False)

            if not prompt and messages:
                for msg in reversed(messages):
                    if msg.get('role') == 'user' and msg.get('content'):
                        prompt = msg.get('content'); break

            user_id = self._get_user_id(request)

            self.logger(f"[AI Request (Legacy)] Model: {endpoint_id} | Stream: {stream_requested} | User: {user_id}", "INFO")

            loop = asyncio.get_event_loop()

            def run_query():
                return ai_manager.query_ai_by_task(
                    task_type="general", prompt=prompt, endpoint_id=endpoint_id,
                    messages=messages, stream=stream_requested, user_id=user_id
                )

            if stream_requested:
                headers = {
                    'Content-Type': 'text/event-stream',
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Credentials": "true",
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS",
                    "Access-Control-Allow-Headers": "X-API-Key, Content-Type, Authorization, X-Flowork-User-ID, X-Flowork-Engine-ID, X-Signature, X-User-Address, X-Signed-Message, traceparent, x-gateway-token",
                }

                origin = request.headers.get("Origin")
                allowed_origins = {
                    "https://flowork.cloud", "https://momod.flowork.cloud",
                    "http://localhost:5173", "http://localhost:8002",
                    "http://localhost:5001"
                }
                if origin in allowed_origins:
                    headers["Access-Control-Allow-Origin"] = origin

                response = web.StreamResponse(status=200, reason='OK', headers=headers)
                await response.prepare(request)

                padding = " " * 2048
                init_msg = json.dumps({"type": "status", "message": "Initializing Neural Engine..."})
                await response.write(init_msg.encode('utf-8') + padding.encode('utf-8') + b'\n')

                future = loop.run_in_executor(None, run_query)

                while not future.done():
                    try:
                        await asyncio.wait_for(asyncio.shield(future), timeout=10.0)
                        break
                    except asyncio.TimeoutError:
                        status_msg = random.choice(self.LOADING_MESSAGES)
                        status_payload = json.dumps({
                            "type": "status",
                            "message": status_msg
                        })
                        try:
                            await response.write(status_payload.encode('utf-8') + padding.encode('utf-8') + b'\n')
                        except Exception:
                            break

                try:
                    result = await future

                    if isinstance(result, types.GeneratorType):
                        for packet in result:
                            if isinstance(packet, dict):
                                if packet.get("type") == "token":
                                    chunk_payload = json.dumps({
                                        "type": "content",
                                        "chunk": packet.get("content", "")
                                    })
                                    await response.write(chunk_payload.encode('utf-8') + b'\n')

                                elif packet.get("type") == "ping":
                                    status_msg = random.choice(self.LOADING_MESSAGES)
                                    status_payload = json.dumps({"type": "status", "message": status_msg})
                                    await response.write(status_payload.encode('utf-8') + padding.encode('utf-8') + b'\n')

                                elif packet.get("type") == "error":
                                    err_payload = json.dumps({"type": "error", "message": packet.get("content")})
                                    await response.write(err_payload.encode('utf-8') + b'\n')

                            else:
                                if packet:
                                    chunk_payload = json.dumps({
                                        "type": "content",
                                        "chunk": str(packet)
                                    })
                                    await response.write(chunk_payload.encode('utf-8') + b'\n')

                    elif isinstance(result, dict):
                         final_payload = json.dumps({
                             "type": "content",
                             "data": result
                         })
                         await response.write(final_payload.encode('utf-8') + b'\n')
                    else:
                         final_payload = json.dumps({
                             "type": "content",
                             "chunk": str(result)
                         })
                         await response.write(final_payload.encode('utf-8') + b'\n')

                    await response.write_eof()
                    return response

                except Exception as e:
                    self.logger(f"Stream/Query Error: {e}", "ERROR")
                    error_payload = json.dumps({"type": "error", "message": str(e)})
                    try:
                        await response.write(error_payload.encode('utf-8') + b'\n')
                        await response.write_eof()
                    except: pass
                    return response

            else:
                result = await loop.run_in_executor(None, run_query)

                if isinstance(result, dict):
                    status = 500 if "error" in result else 200
                    return self._json_response(result, status=status)
                else:
                    return self._json_response({"response": str(result)})

        except Exception as e:
            self.logger(f"[AI Handler Error] {e}", "ERROR")
            return self._json_response({"error": str(e)}, status=500)

    async def handle_get_conversion_status(self, request):
        return self._json_response({"conversions": []}, status=200)

    async def handle_post_model_conversion(self, request):
        converter_service = self.service_instance.model_converter_service
        if not converter_service:
            try:
                converter_service = self.kernel.get_service("model_converter_service")
            except: pass

            if not converter_service:
                return self._json_response({"error": "Converter Service unavailable"}, status=503)

        try:
            body = await request.json()
            if not body: return self._json_response({"error": "Missing JSON body"}, status=400)

            result = converter_service.start_conversion_job(
                model_id=body.get("model_id"),
                quantization=body.get("quantization", "q4_k_m")
            )

            return self._json_response(result)

        except Exception as e:
            return self._json_response({"error": str(e)}, status=500)

    async def handle_model_upload(self, request):
        return self._json_response({"error": "Upload via API not supported"}, status=200)

    async def handle_post_model_requantize(self, request):
        return self._json_response({"error": "Requantization not supported"}, status=200)

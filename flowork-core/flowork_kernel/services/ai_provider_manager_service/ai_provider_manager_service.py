########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\ai_provider_manager_service\ai_provider_manager_service.py total lines 741 
########################################################################

import os
import json
import importlib.util
import subprocess
import sys
import importlib.metadata
import tempfile
import zipfile
import shutil
import traceback
import time
import hashlib
import threading
import select
import asyncio
import uuid
import glob
from datetime import datetime
from aiohttp import web
from ..base_service import BaseService
from flowork_kernel.utils.file_helper import sanitize_filename

try:
    import torch
    from diffusers import StableDiffusionXLPipeline, AutoencoderKL
    DIFFUSERS_AVAILABLE = True
except ImportError:
    DIFFUSERS_AVAILABLE = False

try:
    importlib.metadata.version("llama-cpp-python")
    LLAMA_CPP_AVAILABLE = True
except importlib.metadata.PackageNotFoundError:
    LLAMA_CPP_AVAILABLE = False

class AIProviderManagerService(BaseService):
    def __init__(self, kernel, service_id: str):
        super().__init__(kernel, service_id)

        possible_provider_paths = [
            "/app/flowork_kernel/ai_providers",
            r"C:\FLOWORK\ai_providers",
            os.path.join(self.kernel.project_root_path, "flowork_kernel", "ai_providers")
        ]

        possible_model_paths = [
            "/app/flowork_kernel/ai_models",
            r"C:\FLOWORK\ai_models",
            os.path.join(self.kernel.project_root_path, "flowork_kernel", "ai_models")
        ]

        self.providers_path = self._resolve_valid_path(possible_provider_paths)
        self.models_path = self._resolve_valid_path(possible_model_paths)

        if self.providers_path:
            os.makedirs(self.providers_path, exist_ok=True)
            if self.providers_path not in sys.path:
                sys.path.insert(0, self.providers_path)

        if self.models_path: os.makedirs(self.models_path, exist_ok=True)

        self.loaded_providers = {}
        self.local_models = {}
        self.hf_pipelines = {}

        self.model_load_lock = threading.Lock()
        self.engine_id = os.getenv("FLOWORK_ENGINE_ID", "unknown_engine")

        self.image_output_dir = os.path.join(self.kernel.data_path, "generated_images_by_service")
        os.makedirs(self.image_output_dir, exist_ok=True)

        self.audio_output_dir = os.path.join(self.kernel.data_path, "generated_audio_by_service")
        os.makedirs(self.audio_output_dir, exist_ok=True)

        self.sessions_dir = os.path.join(self.kernel.data_path, "ai_sessions")
        os.makedirs(self.sessions_dir, exist_ok=True)

        self.job_queue = asyncio.Queue()
        self.active_jobs = {} # {job_id: {status: 'QUEUED'|'PROCESSING'|'COMPLETED'|'FAILED', result: ...}}
        self.is_worker_running = False

        self._startup_session_cleanup()

        self.logger.info(f"AI SERVICE READY. Engine ID: {self.engine_id}")
        self.discover_and_load_endpoints()

    def _startup_session_cleanup(self):
        """
        The Janitor: Scans all session files on startup.
        If any session says 'PROCESSING' (which means it crashed/died), set to 'CANCELLED'.
        """
        self.logger.info("🧹 [The Janitor] Cleaning up zombie sessions...")
        try:
            session_files = glob.glob(os.path.join(self.sessions_dir, "*.json"))
            count = 0
            for s_file in session_files:
                try:
                    with open(s_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    if data.get('active_job_status') in ['QUEUED', 'PROCESSING']:
                        data['active_job_status'] = 'CANCELLED'
                        data['active_job_id'] = None

                        data['messages'].append({
                            "role": "assistant",
                            "content": "⚠️ [System] Engine restarted. Previous task was cancelled.",
                            "timestamp": int(time.time() * 1000),
                            "error": True
                        })

                        with open(s_file, 'w', encoding='utf-8') as f:
                            json.dump(data, f, indent=2)
                        count += 1
                except Exception as e:
                    self.logger.error(f"Failed to clean session {s_file}: {e}")

            if count > 0:
                self.logger.warning(f"🧹 [The Janitor] Cleaned {count} zombie sessions.")
        except Exception as e:
            self.logger.error(f"[The Janitor] Critical Error: {e}")

    def create_session(self, title="New Chat", model_id=None):
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        session_data = {
            "id": session_id,
            "title": title,
            "modelId": model_id,
            "created_at": int(time.time() * 1000),
            "updated_at": int(time.time() * 1000),
            "active_job_id": None,
            "active_job_status": "IDLE",
            "messages": []
        }
        self.save_session(session_id, session_data)
        return session_data

    def get_session(self, session_id):
        path = os.path.join(self.sessions_dir, f"{session_id}.json")
        if not os.path.exists(path):
            return None
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None

    def save_session(self, session_id, data):
        path = os.path.join(self.sessions_dir, f"{session_id}.json")
        data['updated_at'] = int(time.time() * 1000)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def delete_session(self, session_id):
        path = os.path.join(self.sessions_dir, f"{session_id}.json")
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

    def list_sessions(self):
        sessions = []
        files = glob.glob(os.path.join(self.sessions_dir, "*.json"))
        files.sort(key=os.path.getmtime, reverse=True)

        for f_path in files[:50]: # Limit to 50 recent
            try:
                with open(f_path, 'r', encoding='utf-8') as f:
                    sessions.append(json.load(f))
            except: pass
        return sessions

    async def submit_job(self, task_type, payload):
        """
        Main Entrypoint for Phase 2 API.
        Puts a job into the Async Queue.
        """
        if not self.is_worker_running:
            asyncio.create_task(self._queue_worker_loop())
            self.is_worker_running = True

        job_id = f"job_{uuid.uuid4().hex[:8]}"
        job_data = {
            "id": job_id,
            "type": task_type,
            "payload": payload,
            "status": "QUEUED",
            "submitted_at": time.time(),
            "position": self.job_queue.qsize() + 1
        }

        self.active_jobs[job_id] = job_data
        await self.job_queue.put(job_id)

        self.logger.info(f"📥 [Neural Queue] Job {job_id} added. Position: {job_data['position']}")
        return job_data

    async def _queue_worker_loop(self):
        """
        The FIFO Worker. Eats jobs one by one.
        """
        self.logger.info("🚀 [Neural Queue] Worker Loop Started.")
        while True:
            try:
                job_id = await self.job_queue.get()

                if job_id not in self.active_jobs:
                    self.job_queue.task_done()
                    continue

                job = self.active_jobs[job_id]
                job['status'] = "PROCESSING"
                job['started_at'] = time.time()

                session_id = job['payload'].get('session_id')
                if session_id:
                    session = self.get_session(session_id)
                    if session:
                        session['active_job_id'] = job_id
                        session['active_job_status'] = "PROCESSING"
                        self.save_session(session_id, session)

                self.logger.info(f"⚙️ [Neural Queue] Processing {job_id} ({job['type']})...")

                try:
                    result = await self._execute_job_logic(job)
                    job['status'] = "COMPLETED"
                    job['result'] = result
                except Exception as e:
                    self.logger.error(f"❌ [Neural Queue] Job {job_id} Failed: {e}")
                    job['status'] = "FAILED"
                    job['error'] = str(e)
                finally:
                    job['completed_at'] = time.time()
                    self.job_queue.task_done()

                    if session_id:
                        session = self.get_session(session_id)
                        if session:
                            session['active_job_status'] = job['status']
                            self.save_session(session_id, session)

            except Exception as e:
                self.logger.error(f"🔥 [Neural Queue] Worker Loop Crash: {e}")
                await asyncio.sleep(1) # Prevent tight loop crash

    async def _execute_job_logic(self, job):
        """
        Router internal execution logic.
        """
        payload = job['payload']
        task_type = job['type']

        prompt = payload.get('prompt')
        endpoint_id = payload.get('endpoint_id')
        messages = payload.get('messages')
        stream = payload.get('stream', False)
        kwargs = payload.get('kwargs', {})

        if task_type == 'generation':
            loop = asyncio.get_event_loop()

            stream_override = False

            return await loop.run_in_executor(
                None,
                lambda: self.query_ai_by_task(
                    "general", prompt, endpoint_id, messages, stream_override, **kwargs
                )
            )
        return {"error": "Unknown task type"}

    def register_routes(self, api_router):
        api_router.add_route('/api/v1/models/local', self._handle_list_local_models, methods=['GET'])
        api_router.add_route('/api/v1/models/local', self._handle_options, methods=['OPTIONS'])
        api_router.add_route('/api/v1/models/rescan', self._handle_rescan_models, methods=['POST'])
        api_router.add_route('/api/v1/models/rescan', self._handle_options, methods=['OPTIONS'])

        api_router.add_route('/api/v1/ai/files/view', self._handle_view_file, methods=['GET'])

    def _handle_options(self, request, **kwargs):
        return {"status": "success", "_headers": self._cors_headers()}

    def _cors_headers(self):
        return {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, x-gateway-token",
            "X-Accel-Buffering": "no",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }

    async def _handle_view_file(self, request):
        try:
            path = request.query.get('path')
            if not path:
                return web.Response(status=400, text="Missing path parameter")

            if ".." in path:
                return web.Response(status=403, text="Invalid path")

            if not os.path.exists(path):
                return web.Response(status=404, text="File not found")

            allowed_prefixes = [self.image_output_dir, self.audio_output_dir]
            abs_path = os.path.abspath(path)
            is_allowed = False
            for prefix in allowed_prefixes:
                if os.path.abspath(prefix) in abs_path:
                    is_allowed = True
                    break

            if "/generated_" not in abs_path and not is_allowed:
                 pass

            return web.FileResponse(abs_path)

        except Exception as e:
            self.logger.error(f"File Serve Error: {e}")
            return web.Response(status=500, text=str(e))

    def _handle_list_local_models(self, request):
        models_list = self.get_loaded_providers_info()
        return {"status": "success", "data": models_list, "_headers": self._cors_headers()}

    def _handle_rescan_models(self, request):
        self.discover_and_load_endpoints()
        return {"status": "success", "message": "AI Models rescanned successfully.", "_headers": self._cors_headers()}

    def _resolve_valid_path(self, candidates):
        for path in candidates:
            if os.path.exists(path): return path
        return candidates[1]

    def discover_and_load_endpoints(self):
        self.logger.warning("--- [AI DISCOVERY] STARTING DEEP SCAN ---")
        self.loaded_providers.clear()
        self.local_models.clear()

        GENERIC_FOLDERS = ['text', 'image', 'images', 'audio', 'video', 'tts', 'stt', 'coding', 'llm', 'ai_models', 'models']

        if os.path.isdir(self.providers_path):
            for root, dirs, files in os.walk(self.providers_path):
                if "manifest.json" in files:
                    provider_dir = root
                    provider_id = os.path.basename(provider_dir)
                    if "__pycache__" in provider_dir: continue
                    try:
                        with open(os.path.join(provider_dir, "manifest.json"), "r", encoding="utf-8") as f:
                            manifest = json.load(f)
                        entry_point = manifest.get("entry_point")
                        if not entry_point: continue

                        parent_dir = os.path.dirname(provider_dir)
                        if parent_dir not in sys.path: sys.path.insert(0, parent_dir)

                        vendor_path = os.path.join(provider_dir, "vendor")
                        path_inserted = False
                        if os.path.isdir(vendor_path) and vendor_path not in sys.path:
                            sys.path.insert(0, vendor_path)
                            path_inserted = True

                        try:
                            module_file, class_name = entry_point.split(".")
                            full_import_name = f"{provider_id}.{module_file}"
                            if full_import_name in sys.modules:
                                module = importlib.reload(sys.modules[full_import_name])
                            else:
                                module = importlib.import_module(full_import_name)
                            ProviderCls = getattr(module, class_name)
                            self.loaded_providers[provider_id] = ProviderCls(self.kernel, manifest)
                            self.logger.info(f"  [PROVIDER LOADED] {manifest.get('name', provider_id)}")
                        except Exception as e:
                            self.logger.error(f"  [PROVIDER ERROR] {provider_id}: {e}")
                        finally:
                            if path_inserted:
                                try: sys.path.remove(vendor_path)
                                except: pass
                    except Exception as e:
                        self.logger.error(f"  [MANIFEST ERROR] {provider_dir}: {e}")

        if os.path.isdir(self.models_path):
            for root, dirs, files in os.walk(self.models_path):
                full_path_lower = root.lower()

                category = "unknown"
                if "text" in full_path_lower or "coding" in full_path_lower: category = "text"
                if "image" in full_path_lower or "video" in full_path_lower: category = "image"
                if "audio" in full_path_lower or "tts" in full_path_lower or "speech" in full_path_lower: category = "audio"

                folder_name = os.path.basename(root)
                use_folder_name = folder_name.lower() not in GENERIC_FOLDERS

                for f in files:
                    if f.lower().endswith(".gguf"):
                        model_path = os.path.join(root, f)
                        file_name_only = os.path.splitext(f)[0]

                        if use_folder_name:
                            model_name = folder_name
                            collision_check_id = f"(Local) {model_name}"
                            if collision_check_id in self.local_models:
                                model_name = f"{folder_name} ({file_name_only})"
                        else:
                            model_name = file_name_only

                        model_id = f"(Local) {model_name}"

                        final_cat = category if category != "unknown" else "text"

                        self.local_models[model_id] = {
                            "full_path": model_path, "type": "gguf", "name": model_name, "category": final_cat
                        }
                        self.logger.info(f"  [MODEL FOUND] GGUF: {model_name}")

                has_config = "config.json" in files
                has_safetensors = any(f.lower().endswith(".safetensors") for f in files)
                has_pytorch = any(f.lower().endswith(".bin") for f in files)

                if has_config and (has_safetensors or has_pytorch):
                    model_name = os.path.basename(root)
                    model_id = f"(Local HF) {model_name}"

                    final_category = category
                    try:
                        with open(os.path.join(root, "config.json"), 'r', encoding='utf-8') as cf:
                            config_data = json.load(cf)
                            archs = config_data.get("architectures", [])
                            arch_str = str(archs).lower()

                            if "causallm" in arch_str or "llama" in arch_str or "mistral" in arch_str or "gpt" in arch_str:
                                final_category = "text"
                            elif "diffusion" in arch_str or "unet" in arch_str:
                                final_category = "image"
                            elif "audio" in arch_str or "speech" in arch_str or "whisper" in arch_str:
                                final_category = "audio"
                    except: pass

                    if final_category == "unknown":
                        if any(x in model_name.lower() for x in ['bert', 'gpt', 'llama', 'mistral', 'qwen', 'phi']):
                            final_category = "text"
                        else:
                            final_category = "image" # Default fallback for safety (old behavior)

                    model_type = "hf_audio_model" if final_category == "audio" else "hf_image_model"
                    if final_category == "text": model_type = "hf_text_model"

                    self.local_models[model_id] = {
                        "full_path": root, "type": model_type, "name": model_name, "category": final_category
                    }
                    self.logger.info(f"  [MODEL FOUND] HF Folder ({final_category}): {model_name}")

                elif not has_config:
                    for f in files:
                        if f.lower().endswith(".safetensors") and "vae" not in f.lower():
                            model_path = os.path.join(root, f)
                            file_name_only = os.path.splitext(f)[0]

                            if use_folder_name:
                                model_name = folder_name
                                collision_check_id = f"(Local SD) {model_name}"
                                if collision_check_id in self.local_models:
                                    model_name = f"{folder_name} ({file_name_only})"
                            else:
                                model_name = file_name_only

                            model_id = f"(Local SD) {model_name}"
                            self.local_models[model_id] = {
                                "full_path": model_path, "type": "hf_image_single_file", "name": model_name, "category": "image"
                            }
                            self.logger.info(f"  [MODEL FOUND] Single Checkpoint: {model_name}")

        self.logger.warning(f"--- DISCOVERY DONE. Providers: {len(self.loaded_providers)} | Models: {len(self.local_models)} ---")

    def get_loaded_providers_info(self) -> list:
        info = []
        for pid, p in self.loaded_providers.items():
            man = p.get_manifest() if hasattr(p, 'get_manifest') else {}
            provider_data = {
                "id": pid, "name": man.get('name', pid), "version": man.get('version', '1.0'),
                "tier": getattr(p, 'TIER', 'free').lower(), "type": "provider"
            }

            try:
                if hasattr(p, 'check_status'):
                    s = p.check_status()
                    if isinstance(s, str) and s.lower() == 'ready':
                        provider_data['status'] = 'ready'
                    elif isinstance(s, tuple) and s[0]:
                        provider_data['status'] = 'ready'
                elif hasattr(p, 'is_ready'):
                    s = p.is_ready()
                    if s is True or (isinstance(s, tuple) and s[0]):
                        provider_data['status'] = 'ready'
            except Exception: pass

            info.append(provider_data)

        for mid, m in self.local_models.items():
            info.append({
                "id": mid, "name": m['name'], "version": "Local",
                "tier": "free", "type": "local_model", "category": m['category'],
                "status": "ready"
            })
        return sorted(info, key=lambda x: x['name'])

    def query_ai_by_task(self, task_type: str, prompt: str, endpoint_id: str = None, messages: list = None, stream: bool = False, **kwargs):
        """
        [Legacy/Direct Executor]
        This function is now wrapped by `_execute_job_logic` for queued jobs,
        but kept accessible for direct synchronous calls if needed.
        """
        target = endpoint_id
        if not target: return {"error": "No AI model selected."}

        self.logger.info(f"[AI Query] Target: {target} | Stream: {stream} | User: {kwargs.get('user_id')}")

        if target in self.loaded_providers:
            p = self.loaded_providers[target]
            if messages: kwargs['messages'] = messages
            return p.generate_response(prompt, stream=stream, **kwargs)

        if target in self.local_models:
            m = self.local_models[target]
            if m['type'] == 'gguf':
                return self._run_gguf(m, prompt, messages, stream=stream)
            if 'image' in m['type']:
                return self._run_diffuser(m, prompt, **kwargs)
            if 'audio' in m['type'] or m['category'] == 'audio':
                return self._run_audio_worker(m, prompt, **kwargs)

            return {"error": f"Model type '{m['type']}' not supported yet."}

        return {"error": f"Endpoint {target} not found."}

    def _construct_contextual_prompt(self, messages, new_prompt):
        if not messages: return new_prompt
        full_text = ""
        for msg in messages:
            role = msg.get('role', 'User').capitalize()
            content = msg.get('content', '')
            full_text += f"{role}: {content}\n"
        if not any(m.get('content') == new_prompt for m in messages):
             full_text += f"User: {new_prompt}\n"
        full_text += "Assistant: "
        return full_text

    def _run_gguf(self, model_data, prompt, messages=None, stream=False):
        if not LLAMA_CPP_AVAILABLE: return {"error": "llama-cpp-python not installed."}
        path = model_data['full_path']
        worker = os.path.join(self.kernel.project_root_path, "flowork_kernel", "workers", "ai_worker.py")
        gpu = self.loc.get_setting("ai_gpu_layers", 40)

        final_input = prompt
        if messages:
            final_input = self._construct_contextual_prompt(messages, prompt)

        cmd = [sys.executable, "-u", worker, path, str(gpu)]

        if stream:
            return self._stream_gguf_process(cmd, final_input)

        try:
            res = subprocess.run(cmd, input=final_input, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=1800)
            if res.returncode == 0: return {"type": "text", "data": res.stdout}
            return {"type": "text", "data": f"Error: {res.stderr}"}
        except Exception as e: return {"error": str(e)}

    def _run_audio_worker(self, model_data, prompt, **kwargs):
        path = model_data['full_path']
        worker = os.path.join(self.kernel.project_root_path, "flowork_kernel", "workers", "ai_worker.py")

        cmd = [sys.executable, "-u", worker, path]

        try:
            res = subprocess.run(cmd, input=prompt, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=300)

            if res.returncode != 0:
                self.logger.error(f"[Audio Worker Fail] {res.stderr}")
                return {"error": f"Audio Gen Failed: {res.stderr}"}

            try:
                result = json.loads(res.stdout)
                if 'error' in result: return {"error": result['error']}

                if 'audio_path' in result:
                    temp_path = result['audio_path']

                    user_id = kwargs.get('user_id')
                    if not user_id or user_id == "None": user_id = 'public'
                    safe_user_id = sanitize_filename(user_id)

                    user_dir = os.path.join(self.audio_output_dir, safe_user_id)
                    os.makedirs(user_dir, exist_ok=True)

                    filename = os.path.basename(temp_path)
                    final_path = os.path.join(user_dir, filename)

                    if temp_path != final_path:
                        shutil.move(temp_path, final_path)

                    safe_path_url = final_path.replace(os.sep, '/')

                    url_with_engine = f"/api/v1/ai/files/view?path={safe_path_url}&engine_id={self.engine_id}"

                    return {"type": "audio", "data": final_path, "url": url_with_engine}

                return {"type": "json", "data": result}

            except json.JSONDecodeError:
                return {"error": f"Invalid JSON from worker: {res.stdout}"}

        except Exception as e:
            return {"error": f"System Error: {str(e)}"}

    def _stream_gguf_process(self, cmd, input_text):
        try:
            process = subprocess.Popen(
                cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=sys.stderr,
                text=False, bufsize=0
            )
            if input_text:
                process.stdin.write(input_text.encode('utf-8'))
                process.stdin.close()

            self.logger.warning("!!! [AI STREAM] Connected. Waiting for tokens... !!!")

            while True:
                reads = [process.stdout.fileno()]
                try:
                    ret = select.select(reads, [], [], 1.0)
                except (ValueError, OSError):
                    break

                if reads[0] in ret[0]:
                    char = process.stdout.read(1)
                    if not char:
                        if process.poll() is not None: break
                        continue
                    try:
                        yield {"type": "token", "content": char.decode('utf-8', errors='replace')}
                    except Exception: pass
                else:
                    yield {"type": "ping"}

            if process.returncode != 0 and process.returncode is not None:
                err = f"Worker exited with code {process.returncode}."
                self.logger.error(f"[AI Worker Error] {err}")
                yield {"type": "error", "content": f"\n[System Error: {err}]"}

        except Exception as e:
            self.logger.error(f"Streaming Exception: {e}")
            yield {"type": "error", "content": f"[System Error: {str(e)}]"}

    def _run_diffuser(self, model_data, prompt, **kwargs):
        if not DIFFUSERS_AVAILABLE: return {"error": "Diffusers/Torch not installed on this Core."}
        name = model_data['name']

        with self.model_load_lock:
            if name not in self.hf_pipelines:
                self.logger.info(f"Loading Image Model: {name} (This may take time)...")
                try:
                    path = model_data['full_path']
                    device = "cuda" if torch.cuda.is_available() else "cpu"
                    dtype = torch.float16 if device == "cuda" else torch.float32

                    vae = None
                    if os.path.isdir(path):
                        vae_path = os.path.join(path, "vae")
                    else:
                        vae_path = os.path.join(os.path.dirname(path), "vae")

                    if os.path.isdir(vae_path):
                        self.logger.info(f"Found local VAE at: {vae_path}")
                        try:
                            vae = AutoencoderKL.from_pretrained(vae_path, torch_dtype=dtype).to(device)
                        except Exception as vae_err:
                            self.logger.warning(f"Failed to load VAE: {vae_err}")
                            vae = None

                    load_args = {"torch_dtype": dtype}
                    if vae is not None:
                        load_args["vae"] = vae

                    if model_data['type'] == 'hf_image_single_file':
                        pipe = StableDiffusionXLPipeline.from_single_file(path, **load_args)
                    else:
                        pipe = StableDiffusionXLPipeline.from_pretrained(path, **load_args)

                    if device == "cuda":
                        try:
                            pipe.enable_model_cpu_offload()
                            self.logger.info("Enabled Model CPU Offload.")
                        except Exception as e:
                            self.logger.warning(f"CPU Offload failed: {e}")
                            pipe.to("cuda")

                    self.hf_pipelines[name] = pipe
                    self.logger.info(f"Model {name} Loaded successfully.")
                except Exception as e:
                    self.logger.error(f"Model Load Failed: {e}")
                    return {"error": f"Failed to load model {name}. Details: {str(e)}"}

        try:
            negative = kwargs.get('negative_prompt', 'blurry, low quality, ugly, deformed')
            pipe = self.hf_pipelines[name]

            img = pipe(
                prompt=prompt, negative_prompt=negative,
                width=1024, height=1024, num_inference_steps=30
            ).images[0]

            user_id = kwargs.get('user_id')
            if not user_id or user_id == "None":
                user_id = 'public'

            safe_user_id = sanitize_filename(user_id)
            user_dir = os.path.join(self.image_output_dir, safe_user_id)
            os.makedirs(user_dir, exist_ok=True)

            filename = f"gen_{int(time.time())}.png"
            filepath = os.path.join(user_dir, filename)
            img.save(filepath)

            safe_path_url = filepath.replace(os.sep, '/')

            url_with_engine = f"/api/v1/ai/files/view?path={safe_path_url}&engine_id={self.engine_id}"

            return {"type": "image", "data": filepath, "url": url_with_engine}
        except Exception as e:
            return {"error": f"Generation failed: {str(e)}"}

    def install_component(self, zip_path): return False, "Manual install only."
    def uninstall_component(self, comp_id): return False, "Manual uninstall only."

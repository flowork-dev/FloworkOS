########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\ai_provider_manager_service\ai_provider_manager_service.py total lines 391 
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
            "/app/flowork_kernel/ai_providers",       # Docker Internal Path
            r"C:\FLOWORK\ai_providers",               # Windows Absolute Path
            os.path.join(self.kernel.project_root_path, "flowork_kernel", "ai_providers") # Relative
        ]

        possible_model_paths = [
            "/app/flowork_kernel/ai_models",          # Docker Internal Path
            r"C:\FLOWORK\ai_models",                  # Windows Absolute Path
            os.path.join(self.kernel.project_root_path, "flowork_kernel", "ai_models") # Relative
        ]

        self.providers_path = self._resolve_valid_path(possible_provider_paths)
        self.models_path = self._resolve_valid_path(possible_model_paths)

        if self.providers_path: os.makedirs(self.providers_path, exist_ok=True)
        if self.models_path: os.makedirs(self.models_path, exist_ok=True)

        self.loaded_providers = {}
        self.local_models = {}
        self.hf_pipelines = {}

        self.image_output_dir = os.path.join(self.kernel.data_path, "generated_images_by_service")
        os.makedirs(self.image_output_dir, exist_ok=True)

        self.logger.info(f"AI SERVICE READY (STREAMING ENABLED).")
        self.logger.info(f"  > PROVIDERS ROOT: {self.providers_path}")
        self.logger.info(f"  > MODELS ROOT:    {self.models_path}")

        self.discover_and_load_endpoints()

    def register_routes(self, api_router):
        api_router.add_route('/api/v1/models/local', self._handle_list_local_models, methods=['GET'])
        api_router.add_route('/api/v1/models/local', self._handle_options, methods=['OPTIONS'])

        api_router.add_route('/api/v1/models/rescan', self._handle_rescan_models, methods=['POST'])
        api_router.add_route('/api/v1/models/rescan', self._handle_options, methods=['OPTIONS'])


    def _handle_options(self, request, **kwargs):
        return {
            "status": "success",
            "message": "Preflight OK",
            "_headers": self._cors_headers()
        }

    def _cors_headers(self):
        return {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, x-gateway-token"
        }

    def _handle_list_local_models(self, request):
        models_list = []
        for model_id, info in self.local_models.items():
            models_list.append({
                "id": model_id,
                "name": info.get("name"),
                "type": info.get("type"),
                "category": info.get("category", "text"),
                "path": info.get("full_path")
            })

        return {
            "status": "success",
            "data": models_list,
            "_headers": self._cors_headers()
        }

    def _handle_rescan_models(self, request):
        self.discover_and_load_endpoints()
        return {
            "status": "success",
            "message": "AI Models rescanned successfully.",
            "_headers": self._cors_headers()
        }


    def _resolve_valid_path(self, candidates):
        for path in candidates:
            if os.path.exists(path):
                return path
        return candidates[1]

    def discover_and_load_endpoints(self):
        self.logger.warning("--- [AI DISCOVERY] STARTING DEEP SCAN ---")
        self.loaded_providers.clear()
        self.local_models.clear()
        self.hf_pipelines.clear()

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

                        vendor_path = os.path.join(provider_dir, "vendor")
                        path_inserted = False
                        if os.path.isdir(vendor_path) and vendor_path not in sys.path:
                            sys.path.insert(0, vendor_path)
                            path_inserted = True

                        try:
                            module_file, class_name = entry_point.split(".")
                            module_path = os.path.join(provider_dir, f"{module_file}.py")

                            if os.path.exists(module_path):
                                spec_name = f"provider_module_{provider_id}_{int(time.time())}"
                                spec = importlib.util.spec_from_file_location(spec_name, module_path)
                                module = importlib.util.module_from_spec(spec)
                                sys.modules[spec_name] = module
                                spec.loader.exec_module(module)

                                ProviderCls = getattr(module, class_name)
                                self.loaded_providers[provider_id] = ProviderCls(self.kernel, manifest)
                                self.logger.info(f"  [PROVIDER] Loaded: {manifest.get('name', provider_id)}")
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
                if "audio" in full_path_lower: category = "audio"

                for f in files:
                    if f.lower().endswith(".gguf"):
                        model_path = os.path.join(root, f)
                        model_name = os.path.splitext(f)[0]
                        model_id = f"(Local) {model_name}"

                        self.local_models[model_id] = {
                            "full_path": model_path,
                            "type": "gguf",
                            "name": model_name,
                            "category": category if category != "unknown" else "text"
                        }
                        self.logger.info(f"  [MODEL] Found GGUF: {model_name}")

                has_config = "config.json" in files
                has_safetensors = any(f.lower().endswith(".safetensors") for f in files)

                if has_config and has_safetensors:
                    model_name = os.path.basename(root)
                    model_id = f"(Local HF) {model_name}"
                    self.local_models[model_id] = {
                        "full_path": root,
                        "type": "hf_image_model",
                        "name": model_name,
                        "category": "image" if category == "unknown" else category
                    }
                    self.logger.info(f"  [MODEL] Found HF Folder: {model_name}")

                elif not has_config:
                    for f in files:
                        if f.lower().endswith(".safetensors") and "vae" not in f.lower():
                            model_path = os.path.join(root, f)
                            model_name = os.path.splitext(f)[0]
                            model_id = f"(Local SD) {model_name}"
                            self.local_models[model_id] = {
                                "full_path": model_path,
                                "type": "hf_image_single_file",
                                "name": model_name,
                                "category": "image"
                            }
                            self.logger.info(f"  [MODEL] Found Checkpoint: {model_name}")

        self.logger.warning(f"--- DISCOVERY DONE. Total: {len(self.loaded_providers) + len(self.local_models)} ---")

    def get_provider(self, provider_id: str):
        return self.loaded_providers.get(provider_id)

    def get_available_providers(self) -> dict:
        provider_names = {}
        for pid, p in self.loaded_providers.items():
            provider_names[pid] = p.get_provider_name()
        for mid, m in self.local_models.items():
            provider_names[mid] = f"{m['name']} [LOCAL]"
        return provider_names

    def get_loaded_providers_info(self) -> list:
        info = []
        for pid, p in self.loaded_providers.items():
            man = p.get_manifest() if hasattr(p, 'get_manifest') else {}
            info.append({
                "id": pid, "name": man.get('name', pid),
                "version": man.get('version', '1.0'), "tier": getattr(p, 'TIER', 'free').lower(),
                "type": "provider"
            })
        for mid, m in self.local_models.items():
            info.append({
                "id": mid, "name": m['name'], "version": "Local",
                "tier": "free", "type": "local_model", "category": m['category']
            })
        return sorted(info, key=lambda x: x['name'])

    def query_ai_by_task(self, task_type: str, prompt: str, endpoint_id: str = None, messages: list = None, stream: bool = False, **kwargs):
        target = endpoint_id or self.loc.get_setting(f"ai_model_for_{task_type}") or self.loc.get_setting("ai_model_for_other")
        if not target: return {"error": "No AI model selected."}

        self.logger.info(f"[AI Query] Target: {target} | Stream: {stream}")

        if target in self.loaded_providers:
            p = self.loaded_providers[target]
            ready, msg = p.is_ready()
            if not ready: return {"error": f"Provider not ready: {msg}"}

            if messages:
                kwargs['messages'] = messages

            return p.generate_response(prompt, stream=stream, **kwargs)

        if target in self.local_models:
            m = self.local_models[target]

            if m['type'] == 'gguf':
                return self._run_gguf(m, prompt, messages, stream=stream)

            if 'image' in m['type']:
                return self._run_diffuser(m, prompt, **kwargs)

        return {"error": f"Endpoint {target} not found."}

    def _construct_contextual_prompt(self, messages, new_prompt):
        if not messages:
            return new_prompt
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

        cmd = [sys.executable, worker, path, str(gpu)]

        if stream:
            return self._stream_gguf_process(cmd, final_input)

        try:
            res = subprocess.run(cmd, input=final_input, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=600)
            if res.returncode == 0: return {"type": "text", "data": res.stdout}
            return {"type": "text", "data": f"Error: {res.stderr}"}
        except Exception as e: return {"error": str(e)}

    def _stream_gguf_process(self, cmd, input_text):
        try:
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, # We might want to log stderr separately
                text=True,
                encoding='utf-8',
                errors='replace',
                bufsize=0 # Unbuffered is key!
            )

            if input_text:
                process.stdin.write(input_text)
                process.stdin.close() # Close stdin to signal EOF to the worker so it starts processing

            while True:
                char = process.stdout.read(1)

                if not char and process.poll() is not None:
                    break

                if char:
                    yield char

            if process.returncode != 0:
                err = process.stderr.read()
                if err:
                    self.logger.error(f"[AI Worker Error] {err}")

        except Exception as e:
            self.logger.error(f"Streaming Error: {e}")
            yield f"[System Error: {str(e)}]"

    def _run_diffuser(self, model_data, prompt, **kwargs):
        if not DIFFUSERS_AVAILABLE: return {"error": "Diffusers/Torch not installed."}
        name = model_data['name']

        if name not in self.hf_pipelines:
            self.logger.info(f"Loading Pipeline: {name}...")
            try:
                path = model_data['full_path']
                device = "cuda" if torch.cuda.is_available() else "cpu"
                dtype = torch.float16 if device == "cuda" else torch.float32

                vae_path = None
                possible_vaes = [
                    os.path.join(self.models_path, "vae", "sdxl-vae-fp16-fix"),
                    os.path.join(os.path.dirname(path), "vae")
                ]
                for v in possible_vaes:
                    if os.path.isdir(v): vae_path = v; break

                vae = AutoencoderKL.from_pretrained(vae_path, torch_dtype=dtype).to(device) if vae_path else None

                if model_data['type'] == 'hf_image_single_file':
                    pipe = StableDiffusionXLPipeline.from_single_file(path, vae=vae, torch_dtype=dtype).to(device)
                else:
                    pipe = StableDiffusionXLPipeline.from_pretrained(path, torch_dtype=dtype).to(device)

                if device == "cuda": pipe.enable_model_cpu_offload()
                self.hf_pipelines[name] = pipe
            except Exception as e: return {"error": f"Load failed: {e}"}

        try:
            img = self.hf_pipelines[name](prompt=prompt, negative_prompt=kwargs.get('negative_prompt', ''), width=1024, height=1024).images[0]
            fname = f"gen_{int(time.time())}.png"
            out = os.path.join(self.image_output_dir, fname)
            img.save(out)
            return {"type": "image", "data": out}
        except Exception as e: return {"error": str(e)}

    def install_component(self, zip_path): return False, "Manual install only for now."
    def uninstall_component(self, comp_id): return False, "Manual uninstall only."

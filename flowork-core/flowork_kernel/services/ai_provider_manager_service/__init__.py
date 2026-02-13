########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\ai_provider_manager_service\__init__.py total lines 166 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from flowork_kernel.services.base_service import BaseService
import importlib
import os
import logging
import asyncio
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
import uuid
import glob
from datetime import datetime
from aiohttp import web
from flowork_kernel.utils.file_helper import sanitize_filename

class AIProviderManagerService(BaseService):

    def __init__(self, kernel, service_id: str):
        self.cells = {}
        if not hasattr(self, 'logger'):
            self.logger = logging.getLogger('LazyHub')
        super().__init__(kernel, service_id)

        possible_provider_paths = [
            '/app/flowork_kernel/ai_providers',
            'C:\\FLOWORK\\ai_providers',
            os.path.join(self.kernel.project_root_path, 'flowork_kernel', 'ai_providers')
        ]
        possible_model_paths = [
            '/app/flowork_kernel/ai_models',
            'C:\\FLOWORK\\ai_models',
            os.path.join(self.kernel.project_root_path, 'flowork_kernel', 'ai_models')
        ]
        self.providers_path = self._resolve_valid_path(possible_provider_paths)
        self.models_path = self._resolve_valid_path(possible_model_paths)

        if self.providers_path:
            os.makedirs(self.providers_path, exist_ok=True)
            if self.providers_path not in sys.path:
                sys.path.insert(0, self.providers_path)
        if self.models_path:
            os.makedirs(self.models_path, exist_ok=True)

        self.loaded_providers = {}
        self.local_models = {}
        self.hf_pipelines = {}
        self.model_load_lock = threading.Lock()
        self.engine_id = os.getenv('FLOWORK_ENGINE_ID', 'unknown_engine')

        self.image_output_dir = os.path.join(self.kernel.data_path, 'generated_images_by_service')
        os.makedirs(self.image_output_dir, exist_ok=True)
        self.audio_output_dir = os.path.join(self.kernel.data_path, 'generated_audio_by_service')
        os.makedirs(self.audio_output_dir, exist_ok=True)
        self.sessions_dir = os.path.join(self.kernel.data_path, 'ai_sessions')
        os.makedirs(self.sessions_dir, exist_ok=True)

        self.job_queue = asyncio.Queue()
        self.active_jobs = {}
        self.is_worker_running = False

        self._startup_session_cleanup()
        self.logger.info(f'AI SERVICE READY. Engine ID: {self.engine_id}')
        self.discover_and_load_endpoints()

    def run(self, data: dict):
        """
        Pintu masuk utama untuk eksekusi AI.
        Menerima dictionary data dengan kunci 'action'.
        """
        action = data.get('action', 'generate')
        if action == 'generate':
            prompt = data.get('prompt', '')
            provider = data.get('provider')
            model = data.get('model')
            return self.query_ai_by_task(task_type='general', prompt=prompt, endpoint_id=provider or model)

        return {"status": "error", "message": f"Action '{action}' not implemented in service run()"}

    def execute_sync(self, cell_name, *args, **kwargs):
        module = self._load_cell(cell_name)
        return module.run(self, *args, **kwargs)

    async def execute_async(self, cell_name, *args, **kwargs):
        module = self._load_cell(cell_name)
        return await module.run(self, *args, **kwargs)

    def _load_cell(self, cell_name):
        if cell_name not in self.cells:
            try:
                module = importlib.import_module(f".{cell_name}", package=__package__)
                self.cells[cell_name] = module
                if hasattr(self, 'logger'):
                    self.logger.info(f"[LazyHub] ✅ Loaded: {cell_name}.py")
            except Exception as e:
                if hasattr(self, 'logger'):
                    self.logger.error(f"[LazyHub] ❌ Failed to load '{cell_name}': {e}")
                raise e
        return self.cells[cell_name]

    def _startup_session_cleanup(self, *args, **kwargs):
        return self.execute_sync('_startup_session_cleanup', *args, **kwargs)
    def create_session(self, *args, **kwargs):
        return self.execute_sync('create_session', *args, **kwargs)
    def get_session(self, *args, **kwargs):
        return self.execute_sync('get_session', *args, **kwargs)
    def save_session(self, *args, **kwargs):
        return self.execute_sync('save_session', *args, **kwargs)
    def delete_session(self, *args, **kwargs):
        return self.execute_sync('delete_session', *args, **kwargs)
    def list_sessions(self, *args, **kwargs):
        return self.execute_sync('list_sessions', *args, **kwargs)
    async def submit_job(self, *args, **kwargs):
        return await self.execute_async('submit_job', *args, **kwargs)
    async def _queue_worker_loop(self, *args, **kwargs):
        return await self.execute_async('_queue_worker_loop', *args, **kwargs)
    async def _execute_job_logic(self, *args, **kwargs):
        return await self.execute_async('_execute_job_logic', *args, **kwargs)
    def register_routes(self, *args, **kwargs):
        return self.execute_sync('register_routes', *args, **kwargs)
    def _handle_options(self, *args, **kwargs):
        return self.execute_sync('_handle_options', *args, **kwargs)
    def _cors_headers(self, *args, **kwargs):
        return self.execute_sync('_cors_headers', *args, **kwargs)
    async def _handle_view_file(self, *args, **kwargs):
        return await self.execute_async('_handle_view_file', *args, **kwargs)
    def _handle_list_local_models(self, *args, **kwargs):
        return self.execute_sync('_handle_list_local_models', *args, **kwargs)
    def _handle_rescan_models(self, *args, **kwargs):
        return self.execute_sync('_handle_rescan_models', *args, **kwargs)
    def _resolve_valid_path(self, *args, **kwargs):
        return self.execute_sync('_resolve_valid_path', *args, **kwargs)
    def discover_and_load_endpoints(self, *args, **kwargs):
        return self.execute_sync('discover_and_load_endpoints', *args, **kwargs)
    def get_loaded_providers_info(self, *args, **kwargs):
        return self.execute_sync('get_loaded_providers_info', *args, **kwargs)
    def query_ai_by_task(self, *args, **kwargs):
        return self.execute_sync('query_ai_by_task', *args, **kwargs)
    def _construct_contextual_prompt(self, *args, **kwargs):
        return self.execute_sync('_construct_contextual_prompt', *args, **kwargs)
    def _run_gguf(self, *args, **kwargs):
        return self.execute_sync('_run_gguf', *args, **kwargs)
    def _run_audio_worker(self, *args, **kwargs):
        return self.execute_sync('_run_audio_worker', *args, **kwargs)
    def _stream_gguf_process(self, *args, **kwargs):
        return self.execute_sync('_stream_gguf_process', *args, **kwargs)
    def _run_diffuser(self, *args, **kwargs):
        return self.execute_sync('_run_diffuser', *args, **kwargs)
    def install_component(self, *args, **kwargs):
        return self.execute_sync('install_component', *args, **kwargs)
    def uninstall_component(self, *args, **kwargs):
        return self.execute_sync('uninstall_component', *args, **kwargs)

########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\ai_provider_manager_service\discover_and_load_endpoints.py total lines 155 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
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
from flowork_kernel.utils.file_helper import sanitize_filename


def run(hub):
    hub.logger.warning('--- [AI DISCOVERY] STARTING DEEP SCAN ---')
    hub.loaded_providers.clear()
    hub.local_models.clear()
    GENERIC_FOLDERS = ['text', 'image', 'images', 'audio', 'video', 'tts', 'stt', 'coding', 'llm', 'ai_models', 'models']
    if os.path.isdir(hub.providers_path):
        for (root, dirs, files) in os.walk(hub.providers_path):
            if 'manifest.json' in files:
                provider_dir = root
                provider_id = os.path.basename(provider_dir)
                if '__pycache__' in provider_dir:
                    continue
                try:
                    with open(os.path.join(provider_dir, 'manifest.json'), 'r', encoding='utf-8') as f:
                        manifest = json.load(f)
                    entry_point = manifest.get('entry_point')
                    if not entry_point:
                        continue
                    parent_dir = os.path.dirname(provider_dir)
                    if parent_dir not in sys.path:
                        sys.path.insert(0, parent_dir)
                    vendor_path = os.path.join(provider_dir, 'vendor')
                    path_inserted = False
                    if os.path.isdir(vendor_path) and vendor_path not in sys.path:
                        sys.path.insert(0, vendor_path)
                        path_inserted = True
                    try:
                        (module_file, class_name) = entry_point.split('.')
                        full_import_name = f'{provider_id}.{module_file}'
                        if full_import_name in sys.modules:
                            module = importlib.reload(sys.modules[full_import_name])
                        else:
                            module = importlib.import_module(full_import_name)
                        ProviderCls = getattr(module, class_name)
                        hub.loaded_providers[provider_id] = ProviderCls(hub.kernel, manifest)
                        hub.logger.info(f"  [PROVIDER LOADED] {manifest.get('name', provider_id)}")
                    except Exception as e:
                        hub.logger.error(f'  [PROVIDER ERROR] {provider_id}: {e}')
                    finally:
                        if path_inserted:
                            try:
                                sys.path.remove(vendor_path)
                            except:
                                pass
                except Exception as e:
                    hub.logger.error(f'  [MANIFEST ERROR] {provider_dir}: {e}')
    if os.path.isdir(hub.models_path):
        for (root, dirs, files) in os.walk(hub.models_path):
            full_path_lower = root.lower()
            category = 'unknown'
            if 'text' in full_path_lower or 'coding' in full_path_lower:
                category = 'text'
            if 'image' in full_path_lower or 'video' in full_path_lower:
                category = 'image'
            if 'audio' in full_path_lower or 'tts' in full_path_lower or 'speech' in full_path_lower:
                category = 'audio'
            folder_name = os.path.basename(root)
            use_folder_name = folder_name.lower() not in GENERIC_FOLDERS
            for f in files:
                if f.lower().endswith('.gguf'):
                    model_path = os.path.join(root, f)
                    file_name_only = os.path.splitext(f)[0]
                    if use_folder_name:
                        model_name = folder_name
                        collision_check_id = f'(Local) {model_name}'
                        if collision_check_id in hub.local_models:
                            model_name = f'{folder_name} ({file_name_only})'
                    else:
                        model_name = file_name_only
                    model_id = f'(Local) {model_name}'
                    final_cat = category if category != 'unknown' else 'text'
                    hub.local_models[model_id] = {'full_path': model_path, 'type': 'gguf', 'name': model_name, 'category': final_cat}
                    hub.logger.info(f'  [MODEL FOUND] GGUF: {model_name}')
            has_config = 'config.json' in files
            has_safetensors = any((f.lower().endswith('.safetensors') for f in files))
            has_pytorch = any((f.lower().endswith('.bin') for f in files))
            if has_config and (has_safetensors or has_pytorch):
                model_name = os.path.basename(root)
                model_id = f'(Local HF) {model_name}'
                final_category = category
                try:
                    with open(os.path.join(root, 'config.json'), 'r', encoding='utf-8') as cf:
                        config_data = json.load(cf)
                        archs = config_data.get('architectures', [])
                        arch_str = str(archs).lower()
                        if 'causallm' in arch_str or 'llama' in arch_str or 'mistral' in arch_str or ('gpt' in arch_str):
                            final_category = 'text'
                        elif 'diffusion' in arch_str or 'unet' in arch_str:
                            final_category = 'image'
                        elif 'audio' in arch_str or 'speech' in arch_str or 'whisper' in arch_str:
                            final_category = 'audio'
                except:
                    pass
                if final_category == 'unknown':
                    if any((x in model_name.lower() for x in ['bert', 'gpt', 'llama', 'mistral', 'qwen', 'phi'])):
                        final_category = 'text'
                    else:
                        final_category = 'image'
                model_type = 'hf_audio_model' if final_category == 'audio' else 'hf_image_model'
                if final_category == 'text':
                    model_type = 'hf_text_model'
                hub.local_models[model_id] = {'full_path': root, 'type': model_type, 'name': model_name, 'category': final_category}
                hub.logger.info(f'  [MODEL FOUND] HF Folder ({final_category}): {model_name}')
            elif not has_config:
                for f in files:
                    if f.lower().endswith('.safetensors') and 'vae' not in f.lower():
                        model_path = os.path.join(root, f)
                        file_name_only = os.path.splitext(f)[0]
                        if use_folder_name:
                            model_name = folder_name
                            collision_check_id = f'(Local SD) {model_name}'
                            if collision_check_id in hub.local_models:
                                model_name = f'{folder_name} ({file_name_only})'
                        else:
                            model_name = file_name_only
                        model_id = f'(Local SD) {model_name}'
                        hub.local_models[model_id] = {'full_path': model_path, 'type': 'hf_image_single_file', 'name': model_name, 'category': 'image'}
                        hub.logger.info(f'  [MODEL FOUND] Single Checkpoint: {model_name}')
    total_provider_models = 0
    for (pid, p) in hub.loaded_providers.items():
        if hasattr(p, 'list_available_models'):
            try:
                p_models = p.list_available_models()
                total_provider_models += len(p_models) if p_models else 0
            except:
                pass
    hub.logger.warning(f'--- DISCOVERY DONE. Providers: {len(hub.loaded_providers)} | Models (Local): {len(hub.local_models)} | Models (API): {total_provider_models} ---')

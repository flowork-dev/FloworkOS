########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\ai_provider_manager_service\_run_diffuser.py total lines 88 
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


def run(hub, model_data, prompt, **kwargs):
    if not DIFFUSERS_AVAILABLE:
        return {'error': 'Diffusers/Torch not installed on this Core.'}
    name = model_data['name']
    with hub.model_load_lock:
        if name not in hub.hf_pipelines:
            hub.logger.info(f'Loading Image Model: {name} (This may take time)...')
            try:
                path = model_data['full_path']
                device = 'cuda' if torch.cuda.is_available() else 'cpu'
                dtype = torch.float16 if device == 'cuda' else torch.float32
                vae = None
                if os.path.isdir(path):
                    vae_path = os.path.join(path, 'vae')
                else:
                    vae_path = os.path.join(os.path.dirname(path), 'vae')
                if os.path.isdir(vae_path):
                    hub.logger.info(f'Found local VAE at: {vae_path}')
                    try:
                        vae = AutoencoderKL.from_pretrained(vae_path, torch_dtype=dtype).to(device)
                    except Exception as vae_err:
                        hub.logger.warning(f'Failed to load VAE: {vae_err}')
                        vae = None
                load_args = {'torch_dtype': dtype}
                if vae is not None:
                    load_args['vae'] = vae
                if model_data['type'] == 'hf_image_single_file':
                    pipe = StableDiffusionXLPipeline.from_single_file(path, **load_args)
                else:
                    pipe = StableDiffusionXLPipeline.from_pretrained(path, **load_args)
                if device == 'cuda':
                    try:
                        pipe.enable_model_cpu_offload()
                        hub.logger.info('Enabled Model CPU Offload.')
                    except Exception as e:
                        hub.logger.warning(f'CPU Offload failed: {e}')
                        pipe.to('cuda')
                hub.hf_pipelines[name] = pipe
                hub.logger.info(f'Model {name} Loaded successfully.')
            except Exception as e:
                hub.logger.error(f'Model Load Failed: {e}')
                return {'error': f'Failed to load model {name}. Details: {str(e)}'}
    try:
        negative = kwargs.get('negative_prompt', 'blurry, low quality, ugly, deformed')
        pipe = hub.hf_pipelines[name]
        img = pipe(prompt=prompt, negative_prompt=negative, width=1024, height=1024, num_inference_steps=30).images[0]
        user_id = kwargs.get('user_id')
        if not user_id or user_id == 'None':
            user_id = 'public'
        safe_user_id = sanitize_filename(user_id)
        user_dir = os.path.join(hub.image_output_dir, safe_user_id)
        os.makedirs(user_dir, exist_ok=True)
        filename = f'gen_{int(time.time())}.png'
        filepath = os.path.join(user_dir, filename)
        img.save(filepath)
        safe_path_url = filepath.replace(os.sep, '/')
        url_with_engine = f'/api/v1/ai/files/view?path={safe_path_url}&engine_id={hub.engine_id}'
        return {'type': 'image', 'data': filepath, 'url': url_with_engine}
    except Exception as e:
        return {'error': f'Generation failed: {str(e)}'}

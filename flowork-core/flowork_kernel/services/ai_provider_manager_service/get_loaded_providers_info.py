########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\ai_provider_manager_service\get_loaded_providers_info.py total lines 58 
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


def run(hub) -> list:
    info = []
    for (pid, p) in hub.loaded_providers.items():
        man = p.get_manifest() if hasattr(p, 'get_manifest') else {}
        provider_data = {'id': pid, 'name': man.get('name', pid), 'version': man.get('version', '1.0'), 'tier': getattr(p, 'TIER', 'free').lower(), 'type': 'provider'}
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
        except Exception:
            pass
        info.append(provider_data)
        if hasattr(p, 'list_available_models'):
            try:
                avail = p.list_available_models()
                if avail:
                    for am in avail:
                        info.append({'id': am, 'name': am, 'version': 'API', 'tier': provider_data['tier'], 'type': 'api_model', 'category': 'text', 'status': provider_data.get('status', 'ready')})
            except:
                pass
    for (mid, m) in hub.local_models.items():
        info.append({'id': mid, 'name': m['name'], 'version': 'Local', 'tier': 'free', 'type': 'local_model', 'category': m['category'], 'status': 'ready'})
    return sorted(info, key=lambda x: x['name'])

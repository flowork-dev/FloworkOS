########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\app_manager_service\_bind_router_to_instance.py total lines 41 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import json
import importlib.util
import sys
import re
import subprocess
import time
import threading
import requests
from typing import Dict, Any, List, Optional
from flowork_kernel.utils.path_helper import get_apps_directory


def run(hub, instance_obj, app_dir, app_id):
    """
        Standardized to use app_router.py.
        Now with Regex POWER for robust imports! 🛡️
        """
    router_path = os.path.join(app_dir, 'backend', 'app_router.py')
    if os.path.exists(router_path):
        try:
            with open(router_path, 'r') as f:
                source = f.read()
                source = re.sub('from\\s+(?:\\.?)\\s*service\\s+import', 'from app_service import', source)
                source = re.sub('^\\s*import\\s+service\\s*$', 'import app_service as service', source, flags=re.MULTILINE)
                source = source.replace('from flowork_kernel.router import BaseRouter', 'class BaseRouter: def __init__(self, k): self.kernel = k')
            module_name = f'flowork_router_v_final_{app_id}'
            spec = importlib.util.spec_from_file_location(module_name, router_path)
            mod = importlib.util.module_from_spec(spec)
            exec(source, mod.__dict__)
            if hasattr(mod, 'AppRouter'):
                instance_obj.router = mod.AppRouter(instance_obj)
                hub.logger.info(f'🔗 [Router] Success binding app_router to GUI {app_id}')
        except Exception as e:
            hub.logger.error(f'⚠️ [Router] Bind failed for {app_id}: {e}')

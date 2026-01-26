########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\app_manager_service\get_instance.py total lines 66 
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


def run(hub, category: str, item_id: str):
    """
        Retrieves the GUI backend instance.
        Standardized to use app_service.py for the sterile GUI path.
        """
    hub.execute_sync('_touch_app_activity', item_id)
    if item_id in hub.quarantine_registry:
        hub.logger.warning(f"🚫 Access to quarantined app '{item_id}' blocked.")
        return None
    instance_key = f'{category}:{item_id}'
    if instance_key in hub.instances:
        return hub.instances[instance_key]
    app_info = hub.registry['apps']['data'].get(item_id)
    if not app_info:
        return None
    app_folder_path = app_info['path']
    backend_path = os.path.join(app_folder_path, 'backend')
    service_file = os.path.join(backend_path, 'app_service.py')
    if not os.path.exists(service_file):
        hub.logger.warning(f'⚠️ [AppManager] App {item_id} has no app_service.py (GUI path missing).')
        return None
    try:
        module_name = f'flowork_app_exec_{item_id}'
        if app_folder_path not in sys.path:
            sys.path.insert(0, app_folder_path)
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)
        spec = importlib.util.spec_from_file_location(module_name, service_file)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for attr_name in dir(mod):
            attr = getattr(mod, attr_name)
            if isinstance(attr, type) and getattr(attr, '__module__', '') == module_name:
                if attr_name not in ['BaseModule', 'Module', 'BaseAppNode', 'BaseService', 'BaseAppService']:
                    try:
                        new_instance = attr(item_id, {}, hub.kernel)
                    except:
                        try:
                            new_instance = attr(hub.kernel, f'app_{item_id}')
                        except:
                            new_instance = attr()
                    hub.execute_sync('_bind_router_to_instance', new_instance, app_folder_path, item_id)
                    hub.instances[instance_key] = new_instance
                    return new_instance
    except Exception as e:
        hub.logger.error(f'❌ [AppManager] GUI Service init failed for {item_id}: {e}')
    return None

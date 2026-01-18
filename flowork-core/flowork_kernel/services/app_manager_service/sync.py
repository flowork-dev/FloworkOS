########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\app_manager_service\sync.py total lines 53 
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


def run(hub, category: str='apps') -> Dict:
    """
        Only syncs APP entities with GUI and Service backends.
        Strictly ignores any node/workflow definitions.
        """
    target_path = hub.base_app_path
    if not os.path.exists(target_path):
        return {}
    for item_id in os.listdir(target_path):
        item_path = os.path.join(target_path, item_id)
        manifest_file = os.path.join(item_path, 'manifest.json')
        if os.path.isdir(item_path) and os.path.exists(manifest_file):
            try:
                with open(manifest_file, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
                m_id = manifest.get('id')
                if not m_id:
                    continue

                dependencies = manifest.get('dependencies', {})
                if dependencies:
                    lib_manager = hub.get_service('library_manager_service')
                    if lib_manager:
                        for lib, ver in dependencies.items():
                            lib_manager._install_package(lib, ver)

                provided = manifest.get('provided_services', [])
                is_quarantined = m_id in hub.quarantine_registry
                status_label = 'QUARANTINED' if is_quarantined else 'READY'
                app_info = {'manifest': manifest, 'path': item_path, 'type': 'apps', 'is_installed': True, 'icon_url': f'/api/v1/components/app/{m_id}/icon', 'gui_url': f'/api/v1/muscle-assets/{m_id}/assets/index.html', 'services': provided, 'status': status_label}
                hub.registry['apps']['data'][m_id] = app_info
            except Exception:
                pass
    return hub.registry.get('apps', {'data': {}})['data']

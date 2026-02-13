########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\node_manager_service\scan_nodes.py total lines 30 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import json
import importlib.util
import sys
import logging
import inspect
from flowork_kernel.services.base_service import BaseService
from flowork_kernel.utils.path_helper import get_apps_directory


def run(hub):
    hub.nodes_map = {}
    hub.nodes_metadata = []
    if not os.path.exists(hub.base_apps_path):
        hub.logger.warning(f'⚠️ Apps directory not found: {hub.base_apps_path}')
        return
    for app_dir in os.listdir(hub.base_apps_path):
        full_app_path = os.path.join(hub.base_apps_path, app_dir)
        manifest_path = os.path.join(full_app_path, 'manifest.json')
        if os.path.isdir(full_app_path):
            if os.path.exists(manifest_path):
                hub.execute_sync('_process_manifest', full_app_path, manifest_path, app_dir)
            else:
                pass

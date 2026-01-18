########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\node_manager_service\_process_manifest.py total lines 28 
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


def run(hub, app_path, manifest_path, app_folder_name):
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        app_id = manifest.get('id', app_folder_name)
        nodes_def = manifest.get('nodes', [])
        if not nodes_def:
            return
        for node_cfg in nodes_def:
            hub.execute_sync('_load_single_node', app_path, node_cfg, manifest)
    except Exception as e:
        hub.logger.error(f'❌ Failed to parse manifest for {app_folder_name}: {e}')

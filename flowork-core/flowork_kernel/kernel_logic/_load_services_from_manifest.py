########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\kernel_logic\_load_services_from_manifest.py total lines 58 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import sys
import json
import time
import logging
import threading
import queue
import importlib
import datetime
import asyncio
from typing import List, Dict, Any, Callable
import requests
from packaging import version
from flowork_kernel.exceptions import PermissionDeniedError


def run(hub):
    manifest_path = os.path.join(os.path.dirname(__file__), 'services.json')
    hub.execute_sync('write_to_log', f'Kernel: Loading services from manifest: {manifest_path}', 'INFO')
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            services_manifest = json.load(f)
        essential_order = ['integrity_checker_service', 'vitality_service', 'license_manager_service', 'event_bus', 'localization_manager', 'app_runtime', 'app_service', 'state_manager_service', 'permission_manager_service', 'variable_manager', 'preset_manager_service']
        all_service_configs = services_manifest['services']
        loaded_ids = set()
        for service_id in essential_order:
            service_config = next((s for s in all_service_configs if s['id'] == service_id), None)
            if service_config:
                hub.execute_sync('_load_service', service_config)
                loaded_ids.add(service_id)
            else:
                hub.execute_sync('write_to_log', f"Essential service '{service_id}' not found in manifest.", 'WARN')
        for service_config in all_service_configs:
            if service_config['id'] not in loaded_ids:
                if service_config.get('COMMENT'):
                    hub.execute_sync('write_to_log', f"Skipping commented service: {service_config['id']} - {service_config['COMMENT']}", 'INFO')
                    continue
                hub.execute_sync('_load_service', service_config)
        hub.execute_sync('write_to_log', 'Kernel: All services loaded. Creating aliases...', 'DEBUG')
        if 'state_manager_service' in hub.services:
            hub.services['state_manager'] = hub.services['state_manager_service']
            hub.execute_sync('write_to_log', "Alias 'state_manager' created for 'state_manager_service'.", 'SUCCESS')
        if 'preset_manager_service' in hub.services:
            hub.services['preset_manager'] = hub.services['preset_manager_service']
            hub.execute_sync('write_to_log', "Alias 'preset_manager' created for 'preset_manager_service'.", 'SUCCESS')
        if 'variable_manager' in hub.services:
            hub.services['variable_manager_service'] = hub.services['variable_manager']
            hub.execute_sync('write_to_log', "Alias 'variable_manager_service' created for 'variable_manager'.", 'SUCCESS')
    except Exception as e:
        import traceback
        hub.execute_sync('write_to_log', f'CRITICAL ERROR loading services manifest: {e}\n{traceback.format_exc()}', 'CRITICAL')
        raise RuntimeError(f'Could not load services manifest: {e}') from e

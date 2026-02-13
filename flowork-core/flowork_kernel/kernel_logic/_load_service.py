########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\kernel_logic\_load_service.py total lines 62 
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


def run(hub, service_config: Dict[str, str]):
    service_id = service_config['id']
    service_type = service_config.get('type', 'class')
    try:
        if service_type == 'service_workflow':
            preset_path = service_config.get('preset_path')
            if not preset_path:
                hub.execute_sync('write_to_log', f"Failed to load service workflow '{service_id}': 'preset_path' is missing.", 'ERROR')
                return
            hub.services[service_id] = ServiceWorkflowProxy(hub, service_id, preset_path)
        else:
            module_path = service_config['module_path']
            class_name = service_config['class_name']

            try:
                module = importlib.import_module(module_path)
            except ImportError as e:
                parts = module_path.split('.')
                if len(parts) > 1 and parts[-1] == parts[-2]:
                    fallback_path = ".".join(parts[:-1])
                    hub.execute_sync('write_to_log', f"Module {module_path} not found. Trying Hub Fallback: {fallback_path}", 'DEBUG')
                    module = importlib.import_module(fallback_path)
                else:
                    raise e

            ServiceClass = getattr(module, class_name)
            hub.services[service_id] = ServiceClass(hub, service_id)
            if service_id == 'event_bus':
                try:
                    loop = asyncio.get_running_loop()
                    hub.services[service_id].set_main_loop(loop)
                    hub.execute_sync('write_to_log', 'EventBus: Successfully captured running main_loop on creation.', 'SUCCESS')
                except RuntimeError:
                    hub.execute_sync('write_to_log', 'EventBus: No running loop found on creation. Will rely on fallback setter.', 'WARN')
        hub.execute_sync('write_to_log', f"Service '{service_id}' loaded successfully.", 'SUCCESS')
    except Exception as e:
        hub.execute_sync('write_to_log', f"Failed to load service '{service_id}': {e}", 'ERROR')
        critical_services = ['event_bus', 'localization_manager', 'integrity_checker_service', 'vitality_service', 'license_manager_service', 'permission_manager_service', 'state_manager_service', 'variable_manager', 'preset_manager_service', 'app_runtime', 'app_service', 'startup_service', 'gateway_connector_service', 'api_server_service', 'websocket_server_service']
        if service_id in critical_services:
            raise RuntimeError(f"Critical service '{service_id}' failed to load.") from e

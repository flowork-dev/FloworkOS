########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\kernel_logic\hot_reload_components.py total lines 45 
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
    hub.execute_sync('write_to_log', 'Kernel: Hot reload triggered (Unified Mutation)...', 'WARN')
    app_service = hub.execute_sync('get_service', 'app_service', is_system_call=True)
    for cache_file in ['module_index.cache', 'widget_index.cache', 'trigger_index.cache', 'plugin_index.cache', 'tool_index.cache']:
        cache_path = os.path.join(hub.data_path, cache_file)
        if os.path.exists(cache_path):
            try:
                os.remove(cache_path)
            except OSError as e:
                hub.execute_sync('write_to_log', f'Could not remove cache file {cache_path}: {e}', 'WARN')
    if app_service:
        hub.execute_sync('write_to_log', 'Kernel: Reloading categories via unified AppService...', 'INFO')
        for cat in ['modules', 'plugins', 'tools', 'widgets', 'triggers']:
            app_service.sync(cat)
    ai_m = hub.execute_sync('get_service', 'ai_provider_manager_service', is_system_call=True)
    if ai_m:
        ai_m.discover_and_load_endpoints()
    loc_m = hub.execute_sync('get_service', 'localization_manager', is_system_call=True)
    if loc_m:
        loc_m.load_all_languages()
    if hub.event_bus:
        hub.event_bus.publish('COMPONENT_LIST_CHANGED', {'status': 'hot_reloaded'})
    hub.execute_sync('write_to_log', 'Kernel: Hot reload finished.', 'SUCCESS')

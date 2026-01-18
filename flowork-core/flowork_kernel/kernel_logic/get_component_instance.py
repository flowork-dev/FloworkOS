########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\kernel_logic\get_component_instance.py total lines 47 
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


def run(hub, component_id: str) -> Any:
    """
        [MUTATION TOTAL BY FOWORK DEV]
        Refactored to prioritize the Unified AppService registry.
        This fixes the 'No items found' issue by ensuring kernel requests are
        routed through the mutated registry.
        """
    if component_id in hub.globally_disabled_components:
        hub.execute_sync('write_to_log', f"Access to globally disabled component '{component_id}' was blocked.", 'CRITICAL')
        return None
    app_service = hub.execute_sync('get_service', 'app_service', is_system_call=True)
    if app_service:
        manifest = app_service.get_manifest(component_id)
        if manifest:
            raw_cat = manifest.get('type', 'modules')
            category = raw_cat if raw_cat.endswith('s') else f'{raw_cat}s'
            hub.execute_sync('write_to_log', f"Kernel: Resolving component '{component_id}' via category '{category}'", 'DEBUG')
            return app_service.get_instance(category, component_id)
        else:
            for cat in ['modules', 'plugins', 'tools', 'triggers', 'widgets']:
                inst = app_service.get_instance(cat, component_id)
                if inst:
                    return inst
    hub.execute_sync('write_to_log', f"Component '{component_id}' not found in unified app_service registry.", 'ERROR')
    return None

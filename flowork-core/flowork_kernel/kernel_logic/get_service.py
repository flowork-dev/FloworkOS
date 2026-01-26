########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\kernel_logic\get_service.py total lines 34 
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


def run(hub, service_id: str, is_system_call: bool=False) -> Any:
    try:
        service = hub.services.get(service_id)
        if not service:
            hub.execute_sync('write_to_log', f"Service '{service_id}' requested but not found in loaded services!", 'ERROR')
        return service
    except PermissionDeniedError as e:
        hub.execute_sync('write_to_log', f"Permission Denied accessing service '{service_id}': {e}", 'WARN')
        raise e
    except Exception as e:
        hub.execute_sync('write_to_log', f"An unexpected error occurred in get_service for '{service_id}': {e}", 'CRITICAL')
        raise e

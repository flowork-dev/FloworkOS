########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\kernel_logic\stop_all_services.py total lines 41 
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


async def run(hub):
    await hub.execute_async('write_to_log', 'Kernel: Stopping all services...', 'INFO')
    for (service_id, service_instance) in reversed(list(hub.services.items())):
        if hasattr(service_instance, 'stop') and callable(getattr(service_instance, 'stop')):
            try:
                if not isinstance(service_instance, ServiceWorkflowProxy):
                    if asyncio.iscoroutinefunction(service_instance.stop):
                        await service_instance.stop()
                    else:
                        service_instance.stop()
                    await hub.execute_async('write_to_log', f"Service '{service_id}' stopped.", 'DEBUG')
            except Exception as e:
                hub.kernel.write_to_log(f"Error stopping service '{service_id}': {e}", 'ERROR')
    for thread in threading.enumerate():
        if thread != threading.main_thread() and hasattr(thread, 'daemon') and thread.daemon:
            try:
                thread.join(timeout=1.0)
            except RuntimeError:
                pass

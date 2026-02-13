########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\kernel_logic\start_all_services.py total lines 38 
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
    await hub.execute_async('write_to_log', 'Kernel: Minimalist bootloader starting...', 'INFO')
    log_worker_thread = threading.Thread(target=hub._log_queue_worker, daemon=True)
    log_worker_thread.start()
    await hub.execute_async('write_to_log', 'Kernel: Handing control directly to StartupService...', 'INFO')
    try:
        startup_service = await hub.execute_async('get_service', 'startup_service', is_system_call=True)
        if startup_service:
            result = await startup_service.run_startup_sequence()
            await hub.execute_async('write_to_log', f'Startup sequence finished with status: {result}', 'SUCCESS')
        else:
            await hub.execute_async('write_to_log', 'CRITICAL: StartupService not found! Cannot start application.', 'ERROR')
            raise RuntimeError('StartupService is essential for application startup and was not found.')
    except Exception as e:
        await hub.execute_async('write_to_log', f'CRITICAL: Startup sequence failed with an exception: {e}', 'ERROR')
        raise e

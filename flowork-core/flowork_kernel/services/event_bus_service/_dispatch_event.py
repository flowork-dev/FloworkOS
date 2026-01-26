########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\event_bus_service\_dispatch_event.py total lines 34 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import asyncio
import logging
import multiprocessing
import queue
import threading
import time
import traceback
from flowork_kernel.services.base_service import BaseService


def run(hub, event_name, subscriber_id, callback, payload):
    """
        Firewall Callback: Memastikan error di satu App tidak membunuh EventBus.
        """
    try:
        if asyncio.iscoroutinefunction(callback):
            if hub._main_loop and hub._main_loop.is_running():
                asyncio.run_coroutine_threadsafe(callback(event_name, subscriber_id, payload), hub._main_loop)
            else:
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(callback(event_name, subscriber_id, payload))
                except RuntimeError:
                    asyncio.run(callback(event_name, subscriber_id, payload))
        else:
            callback(event_name, subscriber_id, payload)
    except Exception as e:
        hub.logger.error(f"⚠️ DISPATCH ERROR for '{subscriber_id}': {e}")

########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\event_bus_service\run_logic.py total lines 30 
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


def run(hub):
    """
        Loop utama Service.
        Bertugas memonitor kesehatan komponen internal (seperti IPC Thread).
        """
    while hub.is_running:
        if hub.is_main_bus and hub.ipc_queue:
            if hub._ipc_thread is None or not hub._ipc_thread.is_alive():
                if hub.ipc_thread_health:
                    hub.logger.warning('♻️ [Tier 2 Recovery] IPC Thread found DEAD. Respawning...')
                    hub.execute_sync('_start_ipc_listener')
                else:
                    pass
        time.sleep(2)

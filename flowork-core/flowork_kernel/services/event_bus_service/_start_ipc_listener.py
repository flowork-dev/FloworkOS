########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\event_bus_service\_start_ipc_listener.py total lines 24 
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
    """Helper untuk spawn thread listener baru (Re-generation capability)"""
    if hub._ipc_thread and hub._ipc_thread.is_alive():
        return
    hub._stop_event.clear()
    hub._ipc_thread = threading.Thread(target=hub._run_ipc_listener_thread, daemon=True, name='IPC_Listener_Thread')
    hub._ipc_thread.start()
    hub.logger.info('👂 IPC Listener Thread spawned.')

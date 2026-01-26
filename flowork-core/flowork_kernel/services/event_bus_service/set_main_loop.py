########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\event_bus_service\set_main_loop.py total lines 23 
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


def run(hub, loop):
    """Mengaktifkan mode Main Bus dan menyalakan 'Telinga' (IPC Listener)"""
    hub.is_main_bus = True
    hub._main_loop = loop
    hub.logger.info('[MainBus] EventBus set to Main mode. Igniting Neural Listener...')
    if hub.ipc_queue:
        hub.execute_sync('_start_ipc_listener')

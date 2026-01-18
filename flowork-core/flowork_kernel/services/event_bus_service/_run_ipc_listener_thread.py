########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\event_bus_service\_run_ipc_listener_thread.py total lines 41 
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
        [MATA-MATA ABADI] Thread khusus untuk mendengar pesan dari Worker.
        Dilengkapi dengan TIER 2 & 3 Error Handling.
        """
    hub.logger.info('[MainBus] IPC Thread Listener started. Polling queue...')
    hub.ipc_thread_health = True
    while not hub._stop_event.is_set():
        try:
            event_data = hub.ipc_queue.get(timeout=1.0)
            if event_data:
                (event_name, payload, publisher_id) = event_data
                hub.execute_sync('publish', event_name, payload, publisher_id=publisher_id or 'IPC_BRIDGE')
        except queue.Empty:
            continue
        except (EOFError, BrokenPipeError) as e:
            hub.logger.critical(f'🔥 BROKEN PIPE DETECTED! IPC Link Severed: {e}')
            hub.ipc_thread_health = False
            if hasattr(hub, 'handle_injury'):
                hub.execute_sync('handle_injury', e)
            break
        except Exception as e:
            hub.logger.error(f'[MainBus] Error in IPC Thread: {e}')
            time.sleep(1)
    hub.logger.info('[MainBus] IPC Thread Listener STOPPED.')

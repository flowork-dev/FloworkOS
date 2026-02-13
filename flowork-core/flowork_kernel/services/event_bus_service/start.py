########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\event_bus_service\start.py total lines 26 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import time

def run(hub):
    """
    [EventBus Entry Point]
    Mengaktifkan loop monitoring kesehatan (Self-Healing).
    """
    hub.logger.info("🚀 event_bus STARTED with Immortal Matrix.")


    while hub.is_running:
        if hub.is_main_bus and hub.ipc_queue:
            if hub._ipc_thread is None or not hub._ipc_thread.is_alive():
                if hub.ipc_thread_health: # Jika sebelumnya sehat, berarti mati mendadak
                    hub.logger.warning("♻️ [Tier 2 Recovery] IPC Thread found DEAD. Respawning...")
                    hub.execute_sync('_start_ipc_listener')
                else:
                    pass

        time.sleep(2)

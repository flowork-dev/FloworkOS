########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\startup_service\start.py total lines 23 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import sys

def run(hub):
    """
    Inisialisasi Startup Sequence.
    Memanggil auto-install dependencies untuk mensinkronkan Warehouse.
    """
    hub.logger.info("🚀 [Startup] Initiating Core Boot Sequence...")

    try:
        hub.logger.info("🏭 [Startup] Triggering Dependency Factory...")
        hub.execute_sync('_auto_install_dependencies')
    except Exception as e:
        hub.logger.error(f"❌ [Startup] Dependency Sync Failed: {e}")

    hub.logger.info("✅ [Startup] Boot Sequence Complete.")

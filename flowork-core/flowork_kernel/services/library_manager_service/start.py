########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\library_manager_service\start.py total lines 25 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import sys
import sqlite3

def run(hub):
    """
    Inisialisasi Library Manager.
    [GOD MODE] Mengatur jalur Warehouse secara global agar sinkron di semua sel.
    """
    hub.logger.info('🚀 [LibraryManager] Booting Nervous System Logistics...')

    hub.warehouse_path = os.path.join(hub.kernel.data_path, "global_libs")

    if not os.path.exists(hub.warehouse_path):
        os.makedirs(hub.warehouse_path, exist_ok=True)
        hub.logger.info(f"📁 [Warehouse] Created global storage at: {hub.warehouse_path}")


    hub.logger.info('✅ LibraryManager Service Online.')

########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\database_service\maintenance_scheduler.py total lines 45 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import threading
import time
import logging

def run(hub, interval_hours: int = 24):
    """
    Neural Metabolism: Background thread untuk pemeliharaan rutin database.
    Menjamin 'The Iron Bank' tetap kenceng dan ramping secara otomatis.
    """
    def maintenance_loop():
        hub.logger.info(f"💤 [SQL Elite] Maintenance scheduler active. Cycle: every {interval_hours}h.")

        while True:
            try:
                time.sleep(60)

                hub.logger.info("🌙 [SQL Elite] Initiating scheduled Neural Refresh...")

                health = hub.execute_sync('_check_db_integrity')
                if health.get('status') != 'healthy':
                    hub.logger.error("🔥 [Maintenance] Neural Vault is UNHEALTHY! Aborting cleanup to prevent data loss.")
                    continue

                hub.execute_sync('_perform_auto_cleanup', days_retention=30)

                hub.execute_sync('_run_vacuum_process')

                stats = hub.execute_sync('_get_db_stats')
                hub.logger.info(f"✨ [Maintenance Done] DB Size now: {stats['data']['file_size_mb']} MB.")

                time.sleep((interval_hours * 3600) - 60)

            except Exception as e:
                hub.logger.error(f"⚠️ [Maintenance] Metabolism loop interrupted: {e}")
                time.sleep(300) # Jeda 5 menit sebelum coba lagi jika crash

    thread = threading.Thread(target=maintenance_loop, name="NeuralMetabolism", daemon=True)
    thread.start()
    return True

########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\database_service\_perform_auto_cleanup.py total lines 41 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import time
import logging

def run(hub, days_retention: int = 30):
    """
    Protokol Pembersihan Otomatis (Lazarus Purge).
    Menghapus riwayat eksekusi dan job yang sudah basi (> 30 hari).
    Gol: Menjaga database tetap Ringan dan Kuat untuk jutaan user.
    """
    hub.logger.info(f"🧹 [SQL Elite] Initiating auto-cleanup (Retention: {days_retention} days)...")

    limit_date = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time() - (days_retention * 86400)))

    try:
        with hub.execute_sync('transaction') as conn:
            cursor = conn.cursor()

            cursor.execute("DELETE FROM Jobs WHERE created_at < ?", (limit_date,))
            jobs_deleted = cursor.rowcount

            cursor.execute("DELETE FROM Executions WHERE created_at < ?", (limit_date,))
            execs_deleted = cursor.rowcount


            hub.logger.info(f"✅ [Cleanup Done] Purged {jobs_deleted} jobs and {execs_deleted} executions.")
            return {
                "status": "success",
                "purged_jobs": jobs_deleted,
                "purged_executions": execs_deleted
            }

    except Exception as e:
        if hasattr(hub, 'logger'):
            hub.logger.error(f"❌ [Cleanup Failed] Saraf database tersumbat: {e}")
        return {"status": "error", "message": str(e)}

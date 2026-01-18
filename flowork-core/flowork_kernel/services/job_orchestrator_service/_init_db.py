########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\job_orchestrator_service\_init_db.py total lines 38 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import sqlite3
import os

def run(hub, *args, **kwargs):
    """
    Menginisialisasi struktur tabel database job.
    Akses properti hub via 'hub.variabel'
    """
    try:
        with hub.db_lock:
            conn = sqlite3.connect(hub.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    job_type TEXT,
                    payload TEXT,
                    status TEXT,
                    created_at REAL,
                    updated_at REAL,
                    result TEXT,
                    error TEXT
                )
            ''')
            conn.commit()
            conn.close()
            hub.logger.info(f"Database initialized at {hub.db_path}")
            return True
    except Exception as e:
        hub.logger.error(f"Failed to init DB: {e}")
        return False

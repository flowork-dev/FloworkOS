########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\database_service\_run_migration_v4.py total lines 22 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import sqlite3

def run(hub, cursor):
    """(V4) Add user_id to Jobs table with performance indexing."""
    try:
        cursor.execute('ALTER TABLE Jobs ADD COLUMN user_id TEXT')
        hub.logger.info("Added 'user_id' column to 'Jobs' table.")

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_user ON Jobs (user_id);')

    except sqlite3.OperationalError as e:
        if 'duplicate column name' in str(e):
            hub.logger.warning("'user_id' column already exists in 'Jobs'. Skipping.")
        else:
            raise

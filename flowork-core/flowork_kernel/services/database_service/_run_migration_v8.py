########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\database_service\_run_migration_v8.py total lines 30 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import sqlite3

def run(hub, cursor):
    """
    Migration v8: Creating GenericStorage for key-value archiving and state management.
    Fulfilling roadmap: Support for million users with light SQL Elite storage.
    """
    hub.logger.info("🛠️ [SQL Elite] Running Migration v8: Creating GenericStorage...")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS GenericStorage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            key TEXT NOT NULL,
            value TEXT NOT NULL,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL,
            UNIQUE(user_id, key)
        )
    ''')

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_storage_user_key ON GenericStorage (user_id, key)')

    hub.logger.info("✅ [SQL Elite] GenericStorage table created successfully.")

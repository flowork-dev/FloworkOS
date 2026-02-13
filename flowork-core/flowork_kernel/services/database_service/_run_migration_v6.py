########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\database_service\_run_migration_v6.py total lines 24 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import sqlite3

def run(hub, cursor):
    """
    (V6) Migration: Add source_handle and target_handle to Edges for strict routing.
    Menjamin data mengalir ke port yang tepat pada sistem multi-engine.
    """
    try:
        cursor.execute("ALTER TABLE Edges ADD COLUMN source_handle TEXT")
        hub.logger.info("✅ [SQL Elite] Added 'source_handle' column to 'Edges' table.")
    except sqlite3.OperationalError as e:
        if 'duplicate column name' not in str(e): raise e

    try:
        cursor.execute("ALTER TABLE Edges ADD COLUMN target_handle TEXT")
        hub.logger.info("✅ [SQL Elite] Added 'target_handle' column to 'Edges' table.")
    except sqlite3.OperationalError as e:
        if 'duplicate column name' not in str(e): raise e

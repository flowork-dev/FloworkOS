########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\database_service\_run_migration_v5.py total lines 28 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import sqlite3

def run(hub, cursor):
    """
    (R5) Migration: Add strategy and gas_budget_hint to Executions table.
    Optimasi untuk menangani berbagai jenis mesin user secara dinamis.
    """
    try:
        cursor.execute("ALTER TABLE Executions ADD COLUMN strategy TEXT DEFAULT 'default'")
        hub.logger.info("✅ [SQL Elite] Added 'strategy' column to 'Executions' table.")
    except sqlite3.OperationalError as e:
        if 'duplicate column name' in str(e):
            hub.logger.warning("⚠️ Column 'strategy' already exists. Skipping.")
        else: raise e

    try:
        cursor.execute("ALTER TABLE Executions ADD COLUMN gas_budget_hint INTEGER DEFAULT 0")
        hub.logger.info("✅ [SQL Elite] Added 'gas_budget_hint' column to 'Executions' table.")
    except sqlite3.OperationalError as e:
        if 'duplicate column name' in str(e):
            hub.logger.warning("⚠️ Column 'gas_budget_hint' already exists. Skipping.")
        else: raise e

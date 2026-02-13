########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\database_service\create_tables.py total lines 59 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import sqlite3
import logging

DB_SCHEMA_VERSION = 9 # Bumped to version 9 for Neural Knowledge Router

def run(hub):
    """
    Membangun Fondasi Tabel Neural Vault.
    Fix: Menghapus nested call 'create_indexes' untuk mencegah deadlock.
    Added: Migration v8 for hybrid app archiving.
    Added: Migration v9 for Neural Knowledge RAG logic.
    """
    conn = hub.execute_sync('create_connection')
    if not conn:
        hub.logger.error('Cannot create tables. No DB connection.')
        return
    try:
        cursor = conn.cursor()

        cursor.execute('PRAGMA journal_mode=WAL;')
        cursor.execute('PRAGMA synchronous=NORMAL;')

        cursor.execute('\n             CREATE TABLE IF NOT EXISTS DBVersion (\n                 id INTEGER PRIMARY KEY,\n                 version INTEGER NOT NULL\n             )\n             ')
        cursor.execute('SELECT version FROM DBVersion WHERE id = 1')
        row = cursor.fetchone()
        current_version = 0
        if row:
            current_version = row[0]
        else:
            cursor.execute('INSERT INTO DBVersion (id, version) VALUES (1, 0)')

        hub.logger.info(f'Current DB schema version: {current_version}. Required version: {DB_SCHEMA_VERSION}')

        if current_version < 1: hub.execute_sync('_run_migration_v1', cursor)
        if current_version < 2: hub.execute_sync('_run_migration_v2', cursor)
        if current_version < 3: hub.execute_sync('_run_migration_v3', cursor)
        if current_version < 4: hub.execute_sync('_run_migration_v4', cursor)
        if current_version < 5: hub.execute_sync('_run_migration_v5', cursor)
        if current_version < 6: hub.execute_sync('_run_migration_v6', cursor)
        if current_version < 7: hub.execute_sync('_run_migration_v7', cursor)
        if current_version < 8: hub.execute_sync('_run_migration_v8', cursor)
        if current_version < 9: hub.execute_sync('_run_migration_v9', cursor) # Added for RAG

        cursor.execute('UPDATE DBVersion SET version = ? WHERE id = 1', (DB_SCHEMA_VERSION,))
        conn.commit()
        hub.logger.info('Database tables verified/created successfully.')

    except sqlite3.Error as e:
        hub.logger.error(f'Failed to create/verify tables: {e}', exc_info=True)
        if conn: conn.rollback()
    finally:
        if conn: conn.close()

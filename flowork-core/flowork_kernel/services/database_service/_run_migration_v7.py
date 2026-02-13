########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\database_service\_run_migration_v7.py total lines 37 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import sqlite3
import logging
import json
import uuid

def run(hub, cursor):
    """
    (V7) [PHASE 4] The Iron Bank Storage (App Isolation).
    Optimasi: Menggunakan 'WITHOUT ROWID' untuk efisiensi penyimpanan di Otak Robot & Android.
    """
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS app_storage (
            key TEXT NOT NULL,
            owner_app_id TEXT NOT NULL,
            value TEXT, -- Simpan data dalam format JSON
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (key, owner_app_id)
        ) WITHOUT ROWID;
    ''')

    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS trg_app_storage_updated_at
        AFTER UPDATE ON app_storage
        BEGIN
            UPDATE app_storage SET updated_at = CURRENT_TIMESTAMP
            WHERE key = OLD.key AND owner_app_id = OLD.owner_app_id;
        END;
    ''')

    hub.logger.info("🏦 [SQL Elite] 'The Iron Bank' (app_storage) is now ARMED and OPTIMIZED.")

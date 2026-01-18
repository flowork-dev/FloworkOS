########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\database_service\_run_migration_v2.py total lines 40 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import sqlite3
import logging

def run(hub, cursor):
    """
    (V2) Tables for Web3 Auth - Optimized for Million Users & Robot Brain.
    Menjamin 1 user bisa punya banyak engine dan 1 engine bisa dishare ke banyak user.
    """

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS engines (
            engine_id TEXT PRIMARY KEY,
            user_address TEXT NOT NULL, -- Owner Address
            engine_token_hash TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        ) WITHOUT ROWID;
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS engine_shares (
            share_id TEXT PRIMARY KEY,
            engine_id TEXT NOT NULL,
            user_address TEXT NOT NULL, -- Shared User Address
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (engine_id) REFERENCES engines (engine_id) ON DELETE CASCADE
        ) WITHOUT ROWID;
    ''')

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_engines_user ON engines (user_address);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_shares_user ON engine_shares (user_address);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_shares_engine ON engine_shares (engine_id);')

    hub.logger.info("🔐 [SQL Elite] Web3 Auth tables initialized with Parallel Access Optimization.")

########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\database_service\_run_migration_v1.py total lines 65 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import sqlite3

def run(hub, cursor):
    """(V1) Initial tables - Optimized for Robot Brain & High Concurrency."""

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Settings (
            key TEXT PRIMARY KEY,
            value TEXT
        ) WITHOUT ROWID;
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Variables (
            var_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            name TEXT NOT NULL,
            value TEXT,
            is_secret INTEGER DEFAULT 0,
            is_enabled INTEGER DEFAULT 1,
            mode TEXT DEFAULT 'single',
            UNIQUE(user_id, name)
        );
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_vars_user ON Variables (user_id);')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Presets (
            preset_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            workflow_data TEXT,
            user_id TEXT,
            signature TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, name)
        );
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_presets_user ON Presets (user_id);')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prompt_templates (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) WITHOUT ROWID;
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Datasets (
            name TEXT PRIMARY KEY,
            data TEXT
        ) WITHOUT ROWID;
    ''')

    hub.logger.info("✅ [SQL Elite] Initial schema (V1) deployed with WITHOUT ROWID storage.")

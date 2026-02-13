########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\database_service\_run_migration_v3.py total lines 82 
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
    (V3) Tables for Job Queue - Optimized for Robot Brain & Android.
    Menambahkan 'WITHOUT ROWID' untuk efisiensi disk dan Index untuk Auto-Cleanup.
    """
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Workflows (
            workflow_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        ) WITHOUT ROWID;
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Nodes (
            node_id TEXT PRIMARY KEY,
            workflow_id TEXT NOT NULL,
            node_type TEXT NOT NULL,
            config_json TEXT,
            FOREIGN KEY (workflow_id) REFERENCES Workflows (workflow_id) ON DELETE CASCADE
        ) WITHOUT ROWID;
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Edges (
            edge_id INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow_id TEXT NOT NULL,
            source_node_id TEXT NOT NULL,
            target_node_id TEXT NOT NULL,
            FOREIGN KEY (workflow_id) REFERENCES Workflows (workflow_id) ON DELETE CASCADE,
            FOREIGN KEY (source_node_id) REFERENCES Nodes (node_id) ON DELETE CASCADE,
            FOREIGN KEY (target_node_id) REFERENCES Nodes (node_id) ON DELETE CASCADE
        );
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Executions (
            execution_id TEXT PRIMARY KEY,
            workflow_id TEXT NOT NULL,
            user_id TEXT,
            status TEXT DEFAULT 'PENDING',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            finished_at DATETIME,
            FOREIGN KEY (workflow_id) REFERENCES Workflows (workflow_id)
        ) WITHOUT ROWID;
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Jobs (
            job_id TEXT PRIMARY KEY,
            execution_id TEXT NOT NULL,
            node_id TEXT NOT NULL,
            status TEXT DEFAULT 'PENDING',
            input_data TEXT,
            output_data TEXT,
            error_message TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            started_at DATETIME,
            finished_at DATETIME,
            workflow_id TEXT,
            FOREIGN KEY (execution_id) REFERENCES Executions (execution_id) ON DELETE CASCADE,
            FOREIGN KEY (node_id) REFERENCES Nodes (node_id) ON DELETE CASCADE,
            FOREIGN KEY (workflow_id) REFERENCES Workflows (workflow_id) ON DELETE CASCADE
        ) WITHOUT ROWID;
    ''')

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_status ON Jobs (status);')

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_executions_created_at ON Executions (created_at);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON Jobs (created_at);')

    hub.logger.info("⚡ [SQL Elite] Job Queue tables (V3) initialized with WITHOUT ROWID optimization.")

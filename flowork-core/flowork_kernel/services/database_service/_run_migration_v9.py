########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\database_service\_run_migration_v9.py total lines 42 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import sqlite3
import time

def run(hub, cursor):
    """
    Migration v9: Creating NeuralKnowledge and KnowledgeVectors for RAG capabilities.
    Ini adalah fondasi agar AI bisa memiliki 'Long-term Memory' yang terindeks.
    """
    hub.logger.info("🛠️ [SQL Elite] Running Migration v9: Creating Neural Knowledge Tables...")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS NeuralKnowledge (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            content TEXT NOT NULL,
            source TEXT, -- Misal: 'file_abc.txt' atau 'web_url'
            tags TEXT,   -- Metadata tambahan dalam format JSON string
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS KnowledgeVectors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            knowledge_id INTEGER NOT NULL,
            vector_data TEXT NOT NULL, -- Array of floats dalam bentuk JSON
            provider_id TEXT NOT NULL, -- Misal: 'gemini-2.0-flash'
            FOREIGN KEY (knowledge_id) REFERENCES NeuralKnowledge(id) ON DELETE CASCADE
        )
    ''')

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_knowledge_user ON NeuralKnowledge (user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_vector_knowledge_id ON KnowledgeVectors (knowledge_id)')

    hub.logger.info("✅ [SQL Elite] Neural Knowledge tables (v9) created successfully.")

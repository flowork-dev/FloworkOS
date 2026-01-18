########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\database_service\_get_db_stats.py total lines 52 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import sqlite3
import logging

def run(hub):
    """
    Neural Monitor: Mengambil statistik vital database SQL Elite.
    Membantu GUI memantau beban data jutaan user secara real-time.
    """
    stats = {
        "status": "online",
        "file_size_mb": 0,
        "tables": {},
        "schema_version": 0,
        "journal_mode": ""
    }

    try:
        if os.path.exists(hub.db_path):
            file_size = os.path.getsize(hub.db_path)
            stats["file_size_mb"] = round(file_size / (1024 * 1024), 2)

        with hub.execute_sync('transaction') as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT version FROM DBVersion WHERE id = 1")
            row = cursor.fetchone()
            if row: stats["schema_version"] = row[0]

            cursor.execute("PRAGMA journal_mode")
            stats["journal_mode"] = cursor.fetchone()[0]

            vital_tables = ['app_storage', 'Jobs', 'Executions', 'Variables', 'Engines']
            for table in vital_tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    stats["tables"][table] = cursor.fetchone()[0]
                except:
                    stats["tables"][table] = "N/A"

        hub.logger.info(f"📊 [SQL Elite] Stats collected. DB Size: {stats['file_size_mb']} MB")
        return {"status": "success", "data": stats}

    except Exception as e:
        hub.logger.error(f"❌ [SQL Elite] Failed to gather neural stats: {e}")
        return {"status": "error", "message": str(e)}

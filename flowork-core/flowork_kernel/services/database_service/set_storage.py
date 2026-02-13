########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\database_service\set_storage.py total lines 32 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import time
import json

def run(hub, key: str, value: str, user_id: str = "system"):
    """
    Menyimpan data key-value ke GenericStorage.
    Fulfilling roadmap: million users with zero-cost archiving.
    """
    hub.logger.info(f"💾 [SQL Elite] Archiving data: {key} for user: {user_id}")

    now = time.time()
    query = """
        INSERT OR REPLACE INTO GenericStorage (user_id, key, value, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
    """
    params = (user_id, key, value, now, now)

    try:
        with hub.execute_sync('transaction') as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
        return True
    except Exception as e:
        hub.logger.error(f"❌ [DatabaseService] set_storage failed: {e}")
        return False

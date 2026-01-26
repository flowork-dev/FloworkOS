########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\database_service\get_all_storage.py total lines 23 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

def run(hub, user_id="system", limit=500):
    """Fixed signature: direct access to GenericStorage to avoid arg mismatch."""
    hub.logger.info(f"📊 [SQL Elite] Fetching for user: {user_id}")

    query = "SELECT key, value FROM GenericStorage WHERE user_id = ? ORDER BY created_at DESC LIMIT ?"
    try:
        payload = {"user_id": user_id, "limit": limit, "query": query}

        conn = hub.execute_sync('get_connection')
        cursor = conn.cursor()
        cursor.execute(query, (user_id, limit))
        rows = cursor.fetchall()

        return [{"key": r[0], "value": r[1]} for r in rows]
    except Exception as e:
        hub.logger.warning(f"⚠️ get_all_storage fallback: {e}")
        return []

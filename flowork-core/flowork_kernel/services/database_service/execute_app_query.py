########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\database_service\execute_app_query.py total lines 33 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import logging

def run(hub, app_id: str, query_type: str, collection: str, payload: dict):
    """
    [FIXED] Membolehkan App membaca variabel GLOBAL tanpa hambatan owner_app_id.
    """
    hub.logger.info(f"🏦 [IronBank] Filtering request from {app_id} for {collection}")

    try:
        system_tables = ["users", "system_logs", "engine_vitals", "provided_services"]

        if collection.lower() in system_tables:
            if query_type.lower() in ["delete", "update", "insert"]:
                raise PermissionError(f"Akses Ditolak! App {app_id} dilarang modifikasi tabel sistem.")

        if collection == "app_storage":
            payload["owner_app_id"] = app_id
            hub.logger.info(f"🔒 [IronBank] Scoping storage to: {app_id}")

        elif collection == "variables":
            hub.logger.info(f"🔓 [IronBank] Global Variable access granted for {app_id}")

        return hub.transaction(query_type, collection, payload)

    except Exception as e:
        hub.logger.error(f"❌ [IronBank-Error] {str(e)}")
        return {"status": "error", "message": f"Iron Bank Access Denied: {str(e)}"}

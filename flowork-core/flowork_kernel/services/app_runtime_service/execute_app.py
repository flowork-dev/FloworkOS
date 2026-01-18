########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\app_runtime_service\execute_app.py total lines 29 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import socket
import json
import struct
import time
import asyncio

async def run(hub, app_id, action='run', payload=None, port=None, **kwargs):
    """
    Eksekutor Utama App: Jalur masuk perintah dari SDK/UI ke Muscle (Runner).
    Fix: Meneruskan 'user_id' untuk mendukung Secret Injection (Roadmap Poin 4).
    """
    final_payload = payload or kwargs.get('params') or {}
    final_action = action or kwargs.get('action') or 'run'
    user_id = kwargs.get('user_id') or hub.kernel.context.get('user_id')

    hub.logger.info(f"🚀 [Muscle] Directing order to App: {app_id} (Action: {final_action}) for User: {user_id}")

    try:
        return await hub.execute_async('execute_service_action', app_id, final_action, final_payload, user_id=user_id)

    except Exception as e:
        hub.logger.error(f"❌ [Runtime] Order failed for {app_id}: {e}")
        return {"status": "error", "error": str(e)}

########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\event_bus_service\publish.py total lines 59 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import asyncio
import logging
import multiprocessing
import queue
import threading
import time
import json

def run(hub, event_name: str, payload: dict, publisher_id: str='SYSTEM'):
    """
    Menyiarkan sinyal saraf ke seluruh tubuh (Internal & Eksternal).
    """
    if event_name not in ['WORKFLOW_EXECUTION_UPDATE', 'NODE_STATUS_UPDATE', 'engine_vitals_update', 'core:ping']:
        hub.logger.debug(f"[Event] '{event_name}' from '{publisher_id}'")

    if payload and event_name == 'WORKFLOW_LOG_ENTRY':
        hub.logger.info(f"[LOG STREAM] {payload.get('message', '')}")

    try:
        json.dumps(payload, default=str)
    except Exception:
        hub.logger.warning(f"⚠️ [EventBus] Payload for '{event_name}' contains non-serializable data. Sanitizing...")
        payload = {"sanitized_data": str(payload), "warning": "Original payload was unsafe"}

    if not hub.is_main_bus and hub.ipc_queue:
        sent = False
        attempts = 0
        while not sent and attempts < hub.pub_max_retries:
            try:
                hub.ipc_queue.put_nowait((event_name, payload, publisher_id))
                sent = True
            except queue.Full:
                attempts += 1
                if attempts < hub.pub_max_retries:
                    time.sleep(hub.pub_backoff * attempts)
                else:
                    hub.logger.error(f"[{publisher_id}] 🔴 TIER 1 FAIL: IPC Queue FULL. Dropping event '{event_name}'.")
            except Exception as e:
                hub.logger.error(f'[{publisher_id}] Error forwarding IPC: {e}')
                attempts += 1

    current_subscribers = list(hub.subscribers.items())
    for (subscriber_id, (pattern, callback)) in current_subscribers:
        if pattern == '*' or pattern == event_name:
            try:
                hub.execute_sync('_dispatch_event', event_name, subscriber_id, callback, payload)
            except Exception as e:
                hub.logger.error(f"❌ [EventBus] Local Dispatch Error ({subscriber_id}): {e}")

    try:
        hub.execute_sync('_dispatch_to_apps', event_name, payload)
    except Exception as e:
        hub.logger.error(f"⚠️ [EventBus] App Dispatch Error: {e}")

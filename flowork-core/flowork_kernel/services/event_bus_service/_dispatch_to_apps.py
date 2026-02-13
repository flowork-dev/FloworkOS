########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\event_bus_service\_dispatch_to_apps.py total lines 61 
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
import traceback
from flowork_kernel.services.base_service import BaseService


def run(hub, event_name, payload):
    """
    [PHASE 5 OPTIMIZED] Menangani propagasi event ke App via AppRuntime dengan Safety Net.
    Non-blocking execution untuk mencegah Kernel freeze.
    """
    app_targets = hub.app_subscriptions.get(event_name, [])
    if not app_targets:
        return

    if not hub._app_runtime_cache:
        hub._app_runtime_cache = hub.kernel.get_service('app_runtime')
        if not hub._app_runtime_cache:
            hub._app_runtime_cache = hub.kernel.get_service('app_runtime_service')

    if hub._app_runtime_cache:
        for (app_id, action_name) in app_targets:
            try:
                if payload.get('_source_app_id') == app_id:
                    hub.logger.debug(f"🔁 [EventBus] Skipping echo for {app_id}")
                    continue

                hub.logger.info(f"⚡ [NervousSystem] Dispatching '{event_name}' to {app_id}->{action_name}")

                loop = None
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    pass

                if loop and loop.is_running():
                    loop.create_task(hub._app_runtime_cache.trigger_event_handler(app_id, action_name, payload))
                else:
                    dispatch_thread = threading.Thread(
                        target=hub._app_runtime_cache.trigger_event_handler,
                        args=(app_id, action_name, payload),
                        name=f"EventPulse-{app_id}"
                    )
                    dispatch_thread.daemon = True
                    dispatch_thread.start()

            except Exception as e:
                hub.logger.error(f'❌ Failed to trigger App {app_id} (Action: {action_name}): {e}')
                hub.logger.error(traceback.format_exc())
    else:
        hub.logger.warning(f"⚠️ AppRuntime not ready. Cannot dispatch '{event_name}' to apps.")

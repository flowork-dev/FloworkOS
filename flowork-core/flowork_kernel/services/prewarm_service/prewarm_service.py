########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\prewarm_service\prewarm_service.py total lines 37 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import logging
import traceback
from flowork_kernel.services.module_manager_service.module_manager_service import ModuleManagerService
from flowork_kernel.services.logging_service.logging_service import setup_logging
log = setup_logging(__name__, "prewarm_service.log")
def prewarm_models():

    try:
        tasks_to_warm = os.getenv("CORE_WARM_TASKS", "")
        if not tasks_to_warm:
            log.info("[Prewarm] CORE_WARM_TASKS env not set. Skipping pre-warm.")
            return
        tasks = [task.strip() for task in tasks_to_warm.split(",") if task.strip()]
        if not tasks:
            log.info("[Prewarm] No valid tasks found in CORE_WARM_TASKS. Skipping.")
            return
        log.info(f"[Prewarm] Starting pre-warm sequence for {len(tasks)} models...")
        module_manager = ModuleManagerService()
        for task_name in tasks:
            log.info(f"[Prewarm] Warming up: {task_name}...")
            try:
                module_manager.get_instance(task_name)
                log.info(f"[Prewarm] ...OK: {task_name} is now hot.")
            except Exception as e:
                log.error(f"[Prewarm] ...FAILED to warm up {task_name}: {e}")
                log.error(traceback.format_exc())
        log.info("[Prewarm] Pre-warm sequence finished.")
    except Exception as e:
        log.error(f"[Prewarm] CRITICAL: Prewarm service failed unexpectedly: {e}")
        log.error(traceback.format_exc())

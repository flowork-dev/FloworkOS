########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\scheduler_service\scheduler_loop.py total lines 30 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import asyncio
import time
from datetime import datetime

async def run(hub):
    hub.logger.info("💓 [Scheduler] Eternal Pulse loop started.")

    try:
        from croniter import croniter
    except ImportError:
        hub.logger.error("❌ [Scheduler] Library 'croniter' missing! Run: pip install croniter")
        return

    while hub.is_running:
        now = datetime.now()

        for task in hub.active_schedules:
            cron = task['cron']
            if croniter.match(cron, now):
                if time.time() - task['last_run'] > 60:
                    task['last_run'] = time.time()
                    asyncio.create_task(hub.execute("trigger_action", task['app_id'], task['action']))

        await asyncio.sleep(30)

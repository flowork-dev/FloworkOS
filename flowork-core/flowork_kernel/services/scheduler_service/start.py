########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\scheduler_service\start.py total lines 26 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import asyncio

async def run(hub):
    """
    Entry Point Wajib: async def run(hub, *args, **kwargs).
    Logic: Transplantasi dari body start scheduler asli.
    """
    if hub.is_running:
        hub.logger.warning("⚠️ [Scheduler] Service already running.")
        return

    hub.is_running = True
    hub.logger.info("⏰ [Scheduler] Engine starting... Scanning for active rules.")

    await hub.execute("scan_all_apps")

    asyncio.create_task(hub.execute("scheduler_loop"))

    hub.logger.info("✅ [Scheduler] Immortal Pulse Active.")
    return True

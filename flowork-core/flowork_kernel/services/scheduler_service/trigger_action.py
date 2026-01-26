########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\scheduler_service\trigger_action.py total lines 14 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

async def run(hub, app_id, action):
    hub.logger.info(f"🚀 [Scheduler] Time's up! Triggering {app_id}::{action}")
    try:
        muscle = hub.kernel.get_service("app_runtime")
        if muscle:
            await muscle.execute_app(app_id=app_id, action=action, user_id="system")
    except Exception as e:
        hub.logger.error(f"❌ [Scheduler] Trigger failed for {app_id}: {e}")

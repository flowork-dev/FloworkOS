########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\app_manager_service\_ghost_reaper_loop.py total lines 39 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import time

def run(hub):
    """
    Background thread yang memantau App nganggur.
    Fix: Memberikan 'Grace Period' (Masa Tenggang) untuk App yang baru spawn.
    """
    hub.logger.info(f"👻 [GhostReaper] Watching shadows... Timeout: {hub.ghost_timeout}s")
    SPAWN_GRACE_PERIOD = 120 # 2 Menit perlindungan untuk App baru

    while True:
        try:
            time.sleep(10)
            now = time.time()
            active_apps = list(hub.app_activity.items())

            for app_id, last_active in active_apps:
                if app_id.startswith("system_"): continue

                started_at = 0
                if hasattr(hub, 'instances') and app_id in hub.instances:
                    started_at = hub.instances[app_id].get('started_at', 0)

                if (now - started_at) < SPAWN_GRACE_PERIOD: continue

                if now - last_active > hub.ghost_timeout:
                    hub.logger.info(f"💀 [GhostReaper] App {app_id} is idle for too long. Reaping soul...")
                    hub.execute_sync('kill_app', app_id)
                    if app_id in hub.app_activity: del hub.app_activity[app_id]

        except Exception as e:
            hub.logger.error(f"🔥 [GhostReaper] Loop crashed: {e}")
            time.sleep(5)

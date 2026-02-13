########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\scheduler_service\scan_all_apps.py total lines 24 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import json

async def run(hub):
    apps_data = hub.kernel.get_service("app_service").registry['apps']['data']
    hub.active_schedules = [] # Reset

    for app_id, info in apps_data.items():
        manifest_path = os.path.join(info['path'], 'manifest.json')
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
                    schedules = manifest.get("schedules", [])
                    for entry in schedules:
                        await hub.execute("register_schedule", app_id, entry)
            except Exception as e:
                hub.logger.warning(f"⚠️ [Scheduler] Failed to read manifest for {app_id}: {e}")

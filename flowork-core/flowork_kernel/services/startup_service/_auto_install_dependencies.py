########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\startup_service\_auto_install_dependencies.py total lines 61 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import json
from flowork_kernel.utils.path_helper import get_apps_directory

def run(hub):
    """
    [Roadmap 1 Implementation]
    Otomatis memindai semua aplikasi yang terinstall saat startup.
    Jika ditemukan 'requirements.txt', langsung install ke Global Library Warehouse.
    """
    hub.logger.info("🏭 [DependencyFactory] Starting Global Warehouse sync...")

    apps_dir = get_apps_directory()
    if not os.path.exists(apps_dir):
        hub.logger.warning("⚠️ Apps directory not found.")
        return

    try:
        apps = [d for d in os.listdir(apps_dir) if os.path.isdir(os.path.join(apps_dir, d))]
    except Exception as e:
        hub.logger.error(f"❌ Failed to list apps directory: {e}")
        return

    scan_count = 0
    install_count = 0

    for app_id in apps:
        app_path = os.path.join(apps_dir, app_id)

        req_path_root = os.path.join(app_path, "requirements.txt")
        req_path_backend = os.path.join(app_path, "backend", "requirements.txt")

        target_req_path = None

        if os.path.exists(req_path_root):
            target_req_path = req_path_root
        elif os.path.exists(req_path_backend):
            target_req_path = req_path_backend

        if target_req_path:
            scan_count += 1
            hub.logger.info(f"🔍 [DependencyFactory] Found requirements for: {app_id}")

            try:
                hub.execute_sync(
                    'resolve_dependencies',
                    app_id=app_id,
                    requirements_path=target_req_path,
                    force_reinstall=False
                )
                install_count += 1
            except Exception as e:
                hub.logger.error(f"❌ [DependencyFactory] Failed setup for {app_id}: {e}")

    hub.logger.info(f"✅ [DependencyFactory] Warehouse Sync Complete. Scanned {scan_count} apps, Synced {install_count}.")

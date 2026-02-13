########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\library_manager_service\resolve_dependencies.py total lines 90 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import sys
import hashlib
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed

def run(hub, app_id: str, requirements_path: str, force_reinstall=False):
    """
    Resolves app dependencies and installs them into Warehouse.
    [FIX] Memastikan hub.warehouse_path terdefinisi dengan aman.
    """
    dependency_list = []

    warehouse_path = getattr(hub, 'warehouse_path', os.path.join(hub.kernel.data_path, "global_libs"))

    if os.path.exists(requirements_path):
        try:
            with open(requirements_path, 'r') as f:
                for line in f:
                    req = line.strip()
                    if req and not req.startswith('#'):
                        dependency_list.append(req)
        except Exception as e:
            hub.logger.warning(f"⚠️ [LibraryManager] Failed reading requirements.txt: {e}")

    app_dir = os.path.dirname(requirements_path)
    manifest_path = os.path.join(app_dir, "manifest.json")
    if os.path.exists(manifest_path):
        try:
            import json
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
                deps = manifest.get('dependencies', [])
                if isinstance(deps, list):
                    for d in deps:
                        if d and d.strip(): dependency_list.append(d.strip())
        except: pass

    dependency_list = list(set(dependency_list))
    if not dependency_list: return []

    injected_paths = []
    hub.logger.info(f"📦 [LibraryManager] Validating {len(dependency_list)} libs for {app_id}...")

    try:
        futures = {}
        with ThreadPoolExecutor(max_workers=3) as executor:
            for req in dependency_list:
                lib_name = req.split('==')[0].split('>=')[0].strip().lower()
                req_hash = hashlib.md5(req.encode()).hexdigest()[:8]
                target_dir = os.path.join(warehouse_path, lib_name, req_hash)

                is_corrupt = False
                if os.path.exists(target_dir):
                    if not os.listdir(target_dir):
                        hub.logger.warning(f"🧟 [ZombieKiller] Found EMPTY folder for {lib_name}. Nuking it!")
                        is_corrupt = True
                    elif force_reinstall:
                        hub.logger.warning(f"🔧 [Manual] Force wiping {lib_name}...")
                        is_corrupt = True

                    if is_corrupt:
                        shutil.rmtree(target_dir, ignore_errors=True)

                if not os.path.exists(target_dir):
                    hub.logger.info(f'⬇️ [Auto-Install] Downloading fresh copy: {req} ...')
                    future = executor.submit(hub._install_package, req, target_dir)
                    futures[future] = target_dir
                else:
                    injected_paths.append(target_dir)

            for future in as_completed(futures):
                try:
                    future.result()
                    t_dir = futures[future]
                    if os.path.exists(t_dir) and os.listdir(t_dir):
                        injected_paths.append(t_dir)
                except Exception as e:
                    hub.logger.error(f"❌ [LibraryManager] Error installing lib: {e}")

    except Exception as e:
        hub.logger.error(f'❌ [LibraryManager] Critical error: {e}')

    return injected_paths

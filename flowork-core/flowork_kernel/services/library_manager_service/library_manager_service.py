########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\library_manager_service\library_manager_service.py total lines 73 
########################################################################

import os
import sys
import subprocess
import hashlib
import json
from ..base_service import BaseService

class LibraryManagerService(BaseService):
    def __init__(self, kernel, service_id: str):
        super().__init__(kernel, service_id)
        self.warehouse_path = os.path.join(self.kernel.project_root_path, "data", "global_libs")
        if not os.path.exists(self.warehouse_path):
            os.makedirs(self.warehouse_path)

        self.logger.info(f"📚 [LibraryManager] Warehouse initialized at: {self.warehouse_path}")

    def resolve_dependencies(self, app_id: str, requirements_path: str):
        """
        Membaca requirements.txt App, lalu:
        1. Cek apakah library versi tersebut sudah ada di Gudang.
        2. Kalau belum, install ke Gudang (bukan ke App).
        3. Mengembalikan daftar PATH folder library untuk di-inject.
        """
        if not os.path.exists(requirements_path):
            return []

        injected_paths = []

        try:
            with open(requirements_path, 'r') as f:
                reqs = [line.strip() for line in f if line.strip() and not line.startswith('#')]

            for req in reqs:
                lib_name = req.split('==')[0].split('>=')[0].strip()

                req_hash = hashlib.md5(req.encode()).hexdigest()[:8]
                target_dir = os.path.join(self.warehouse_path, lib_name, req_hash)

                if not os.path.exists(target_dir):
                    self.logger.info(f"📦 [LibraryManager] Installing {req} into Warehouse...")
                    subprocess.check_call([
                        sys.executable, "-m", "pip", "install",
                        req,
                        "--target", target_dir,
                        "--no-user",
                        "--upgrade"
                    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                injected_paths.append(target_dir)

        except Exception as e:
            self.logger.error(f"❌ [LibraryManager] Failed resolving deps for {app_id}: {e}")

        return injected_paths

    def get_injection_paths(self, app_id: str):
        """
        Mengambil daftar path library yang sudah di-resolve untuk App ini.
        (Bisa dikembangkan dengan caching agar tidak baca file terus)
        """
        return []

    def start(self):
        self.logger.info("LibraryManager Service Online.")

    def stop(self):
        pass

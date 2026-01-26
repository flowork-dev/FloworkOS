########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\dependency_warehouse.py total lines 54 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import sys
import hashlib
import subprocess
import logging
from flowork_kernel.services.base_service import BaseService

class DependencyWarehouse(BaseService):
    def __init__(self, kernel, service_id: str):
        super().__init__(kernel, service_id)
        self.logger = logging.getLogger("Kernel.Warehouse")
        self.warehouse_path = os.path.join(self.kernel.data_path, "global_libs")
        os.makedirs(self.warehouse_path, exist_ok=True)

    def resolve_and_install(self, lib_name: str, version: str = "latest"):
        """
        Mengecek ketersediaan lib di gudang, jika tidak ada, download otomatis. [cite: 16, 19]
        """
        target_dir = os.path.join(self.warehouse_path, lib_name.lower(), version)

        if not os.path.exists(target_dir):
            self.logger.info(f"⬇️ [Warehouse] Library {lib_name} ({version}) not found. Fetching...")
            os.makedirs(target_dir, exist_ok=True)
            try:
                req = f"{lib_name}=={version}" if version != "latest" else lib_name
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install",
                    req, "--target", target_dir, "--no-cache-dir"
                ])
                self.logger.info(f"✅ [Warehouse] {lib_name} is now stored in {target_dir}")
            except Exception as e:
                self.logger.error(f"❌ [Warehouse] Failed to fetch {lib_name}: {e}")
                return None

        return target_dir

    def get_injection_paths(self, requirements: list):
        """
        Memberikan daftar path library untuk 'dibisikkan' ke Runner. [cite: 11, 20]
        """
        paths = []
        for req in requirements:
            parts = req.split('==')
            name = parts[0].strip()
            version = parts[1].strip() if len(parts) > 1 else "latest"
            path = self.resolve_and_install(name, version)
            if path: paths.append(path)
        return paths

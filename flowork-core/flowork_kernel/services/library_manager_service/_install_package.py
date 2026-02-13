########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\library_manager_service\_install_package.py total lines 41 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import sys
import subprocess
import hashlib
import json
import threading
from concurrent.futures import ThreadPoolExecutor


def run(hub, req, target_dir):
    """Worker function yang jalan di thread terpisah"""
    try:

        pip_cmd = [
            sys.executable, '-m', 'pip', 'install',
            req,
            '--target', target_dir,
            '--no-user',
            '--upgrade',
            '--no-cache-dir',
            '--prefer-binary',
            '--disable-pip-version-check',
            '--quiet' # Mengurangi overhead I/O log yang gak perlu
        ]


        subprocess.check_call(pip_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        hub.logger.info(f'✅ [LibraryManager] Installed: {req}')
    except Exception as e:
        hub.logger.error(f'❌ [LibraryManager] Install Error {req}: {e}')
        if os.path.exists(target_dir):
            import shutil
            shutil.rmtree(target_dir, ignore_errors=True)
        raise e

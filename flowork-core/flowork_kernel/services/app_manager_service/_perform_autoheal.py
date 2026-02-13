########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\app_manager_service\_perform_autoheal.py total lines 40 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import json
import importlib.util
import sys
import re
import subprocess
import time
import threading
import requests
from typing import Dict, Any, List, Optional
from flowork_kernel.utils.path_helper import get_apps_directory


def run(hub, app_id, app_path):
    """
        Dokter Pribadi: Memanggil LibraryManager untuk re-install dependency.
        """
    hub.logger.info(f"🚑 [AutoHeal] Starting emergency repairs for '{app_id}'...")
    lib_manager = hub.kernel.get_service('library_manager')
    if not lib_manager:
        hub.logger.error('❌ AutoHeal Failed: LibraryManager missing.')
        return False
    req_file = os.path.join(app_path, 'requirements.txt')
    if os.path.exists(req_file):
        try:
            lib_manager.resolve_dependencies(app_id, req_file)
            hub.logger.info(f"✅ [AutoHeal] Repair successful for '{app_id}'.")
            return True
        except Exception as e:
            hub.logger.error(f'❌ [AutoHeal] Repair failed: {e}')
            return False
    else:
        hub.logger.warning(f"⚠️ [AutoHeal] No requirements.txt found for '{app_id}'. Cannot heal.")
        return False

########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\app_manager_service\_check_immune_system.py total lines 41 
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


def run(hub, app_id):
    """
        Mengecek apakah App sehat atau harus dikarantina.
        Return True jika AMAN, Raise Exception jika BAHAYA.
        """
    now = time.time()
    if app_id in hub.quarantine_registry:
        q_data = hub.quarantine_registry[app_id]
        if now - q_data['timestamp'] > 3600:
            del hub.quarantine_registry[app_id]
            hub.logger.info(f"🛡️ [Immune] App '{app_id}' released from quarantine (Time Served).")
        else:
            raise Exception(f"⛔ App '{app_id}' is in QUARANTINE! Reason: {q_data['reason']}")
    history = hub.crash_tracker.get(app_id, [])
    history = [t for t in history if now - t < hub.CRASH_WINDOW]
    history.append(now)
    hub.crash_tracker[app_id] = history
    if len(history) > hub.MAX_RESTARTS:
        hub.quarantine_registry[app_id] = {'reason': 'Crash Loop Detected (>3 restarts/min)', 'timestamp': now}
        hub.logger.error(f"🛡️ [Immune] CRITICAL: App '{app_id}' entered crash loop. QUARANTINED.")
        raise Exception(f"⛔ App '{app_id}' detected in Crash Loop and has been QUARANTINED.")
    return True

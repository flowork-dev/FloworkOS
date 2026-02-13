########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\app_manager_service\start.py total lines 25 
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


def run(hub):
    hub.execute_sync('sync', 'apps')
    if hub.is_ghost_active:
        hub.execute_sync('_setup_neural_listener')
        t = threading.Thread(target=hub._ghost_reaper_loop, daemon=True, name='GhostReaper')
        t.start()

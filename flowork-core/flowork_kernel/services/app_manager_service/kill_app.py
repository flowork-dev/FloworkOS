########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\app_manager_service\kill_app.py total lines 51 
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


def run(hub, app_id: str):
    """Force kill app daemon with Cleanup Signal."""
    if app_id in hub.process_registry:
        port = hub.execute_sync('get_assigned_port', app_id)
        proc = hub.process_registry[app_id]
        try:
            hub.logger.info(f'🧹 [Janitor] Sending cleanup signal to {app_id}...')
            import socket
            import struct
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(2)
            client.connect(('127.0.0.1', port))
            payload = json.dumps({'action': 'cleanup', 'data': {}}).encode('utf-8')
            client.sendall(struct.pack('!I', len(payload)))
            client.sendall(payload)
            client.close()
        except Exception as e:
            pass

        try:
            proc.terminate()
            proc.wait(timeout=2)
        except:
            proc.kill()

        if app_id in hub.process_registry:
            del hub.process_registry[app_id]

        if hasattr(hub, 'port_registry') and app_id in hub.port_registry:
            pass

        hub.logger.info(f'💀 [AppManager] Killed App {app_id}')

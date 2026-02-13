########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\app_manager_service\_setup_neural_listener.py total lines 39 
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
    """
        Mendengarkan event log dari App.
        Jika App nge-log (misal: 'Rendering 50%'), kita anggap dia SIBUK.
        """
    if hasattr(hub.kernel, 'event_bus'):
        try:

            def heartbeat_handler(event_name, event_id, payload_data):
                payload = payload_data.get('payload', payload_data)
                app_id = payload.get('app_id')
                if app_id:
                    clean_id = app_id.replace('runner_', '').replace('app_', '')
                    if clean_id in hub.last_activity:
                        hub.last_activity[clean_id] = time.time()
            hub.kernel.event_bus.subscribe('APP_LOG_STREAM', 'ghost_keeper', heartbeat_handler)
            hub.kernel.event_bus.subscribe('APP_PROGRESS', 'ghost_keeper_prog', heartbeat_handler)
            hub.logger.info('👻 [Ghost] Connected to Nervous System (Smart Keep-Alive Active).')
        except Exception as e:
            hub.logger.warning(f'👻 [Ghost] Failed to attach neural listener: {e}')

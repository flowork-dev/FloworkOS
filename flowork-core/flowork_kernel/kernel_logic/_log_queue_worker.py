########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\kernel_logic\_log_queue_worker.py total lines 48 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import sys
import json
import time
import logging
import threading
import queue
import importlib
import datetime
import asyncio
from typing import List, Dict, Any, Callable
import requests
from packaging import version
from flowork_kernel.exceptions import PermissionDeniedError


def run(hub):
    while True:
        try:
            log_record = hub.log_queue.get()
            if hub.json_logger:
                level_upper = log_record.get('level', 'INFO').upper()
                message = log_record.get('message', '')
                source = log_record.get('source', 'Unknown')
                log_map = {'INFO': hub.json_logger.info, 'SUCCESS': hub.json_logger.info, 'WARN': hub.json_logger.warning, 'ERROR': hub.json_logger.error, 'CRITICAL': hub.json_logger.critical, 'DEBUG': hub.json_logger.debug, 'DETAIL': hub.json_logger.debug}
                log_function = log_map.get(level_upper, hub.json_logger.info)
                log_function(message, extra={'extra_info': {'source': source}})
            if hub.dashboard_socketio:
                try:
                    hub.dashboard_socketio.emit('new_log', log_record, namespace='/dashboard_events')
                except Exception as e_sock:
                    if hub.file_logger:
                        hub.file_logger.error(f'Failed to emit log to dashboard socket: {e_sock}')
            if hub.file_logger:
                hub.file_logger.info(f"[{log_record.get('level', 'INFO').upper()}] [{log_record.get('source', 'Unknown')}] {log_record.get('message', '')}")
            hub.log_queue.task_done()
        except Exception as e:
            if hub.file_logger:
                hub.file_logger.error(f'[LOG WORKER ERROR] {e}')
            else:
                print(f'[LOG WORKER ERROR] {e}')
            time.sleep(1)

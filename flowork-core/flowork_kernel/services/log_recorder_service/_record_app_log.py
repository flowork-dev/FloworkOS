########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\log_recorder_service\_record_app_log.py total lines 31 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import json
import time
import logging
from logging.handlers import RotatingFileHandler
from flowork_kernel.services.base_service import BaseService


def run(hub, payload, *args):
    try:
        data = payload
        if not isinstance(data, dict) and args:
            for arg in args:
                if isinstance(arg, dict):
                    data = arg
                    break
        if not isinstance(data, dict):
            return
        app_id = data.get('app_id', 'unknown_app')
        msg = data.get('message', '')
        pid = data.get('pid', '?')
        log_entry = f'[APP:{app_id}][PID:{pid}] {msg}'
        hub.file_logger.info(log_entry)
    except Exception:
        pass

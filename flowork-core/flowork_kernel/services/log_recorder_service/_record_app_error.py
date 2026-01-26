########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\log_recorder_service\_record_app_error.py total lines 30 
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
        error = data.get('error', 'Unknown Error')
        log_entry = f'[APP_CRASH:{app_id}] ❌ {error}'
        hub.file_logger.error(log_entry)
    except Exception:
        pass

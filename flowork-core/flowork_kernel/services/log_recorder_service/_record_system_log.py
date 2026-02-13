########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\log_recorder_service\_record_system_log.py total lines 39 
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
        if not isinstance(data, (dict, str)) and args:
            for arg in args:
                if isinstance(arg, (dict, str)):
                    data = arg
                    break
        if isinstance(data, str):
            data = {'message': data}
        level = data.get('level', 'INFO').upper() if isinstance(data, dict) else 'INFO'
        source = data.get('source', 'SYSTEM') if isinstance(data, dict) else 'SYSTEM'
        msg = data.get('message', str(data)) if isinstance(data, dict) else str(data)
        node_id = data.get('node_id', '') if isinstance(data, dict) else ''
        log_entry = f'[{source}] {msg}'
        if node_id:
            log_entry = f'[{source}][{node_id}] {msg}'
        if level == 'ERROR' or level == 'CRITICAL':
            hub.file_logger.error(log_entry)
        elif level == 'WARNING':
            hub.file_logger.warning(log_entry)
        else:
            hub.file_logger.info(log_entry)
    except Exception:
        pass

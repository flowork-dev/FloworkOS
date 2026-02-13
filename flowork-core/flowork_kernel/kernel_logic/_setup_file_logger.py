########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\kernel_logic\_setup_file_logger.py total lines 40 
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
    hub.json_logger = logging.getLogger('FloworkJsonLogger')
    hub.json_logger.setLevel(logging.DEBUG)
    if hub.json_logger.hasHandlers():
        hub.json_logger.handlers.clear()
    json_handler = logging.StreamHandler(sys.stdout)
    json_handler.setFormatter(JsonFormatter())
    hub.json_logger.addHandler(json_handler)
    hub.json_logger.propagate = False
    hub.file_logger = logging.getLogger('FloworkFileLogger')
    hub.file_logger.setLevel(logging.DEBUG)
    log_file_path = os.path.join(hub.logs_path, f"flowork_debug_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    if not hub.file_logger.handlers:
        file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] [%(name)s] %(message)s', datefmt='%H:%M:%S')
        file_handler.setFormatter(formatter)
        hub.file_logger.addHandler(file_handler)
        hub.file_logger.propagate = False

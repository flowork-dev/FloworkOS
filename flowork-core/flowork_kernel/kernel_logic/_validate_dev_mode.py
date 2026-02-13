########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\kernel_logic\_validate_dev_mode.py total lines 38 
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


def run(hub) -> bool:
    dev_mode_file = os.path.join(hub.base_path, 'devmode.on')
    if not os.path.exists(dev_mode_file):
        return False
    try:
        with open(dev_mode_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        if content == hub.DEV_MODE_PUBLIC_KEY.strip():
            return True
        else:
            hub._log_dev_mode_on_init = True
            print('[KERNEL-WARN] devmode.on file found, but its content is invalid. DEV MODE WILL NOT ACTIVATE.')
            return False
    except Exception:
        print('[KERNEL-ERROR] Could not read devmode.on file. DEV MODE WILL NOT ACTIVATE.')
        return False

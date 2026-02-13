########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\app_runtime_service\_extract_percent.py total lines 31 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import sys
import json
import time
import socket
import struct
import subprocess
import threading
import asyncio
import queue
import importlib.util
import concurrent.futures
from typing import Dict, Any
from flowork_kernel.services.base_service import BaseService


def run(hub, msg):
    try:
        import re
        match = re.search('(\\d+(\\.\\d+)?)%', msg)
        if match:
            return float(match.group(1))
    except:
        pass
    return 0

########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\api_client\_handle_response.py total lines 27 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import requests
import json
import os
import threading
import time
import random
from flowork_kernel.kernel import Kernel


def run(hub, response):
    if 200 <= response.status_code < 300:
        if response.status_code == 204 or not response.content:
            return (True, {})
        return (True, response.json())
    else:
        try:
            error_data = response.json()
            message = error_data.get('message') or error_data.get('msg') or error_data.get('error_description') or error_data.get('error', 'Unknown API error')
        except json.JSONDecodeError:
            message = response.text
        return (False, message)

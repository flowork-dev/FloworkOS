########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\api_client\delete_component.py total lines 21 
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


def run(hub, component_type: str, component_id: str):
    try:
        response = requests.delete(f'{hub.local_base_url}/{component_type}/{component_id}', headers=hub.execute_sync('_get_local_auth_headers'))
        return hub.execute_sync('_handle_response', response)
    except requests.exceptions.ConnectionError as e:
        return (False, f'Connection to API server failed: {e}')

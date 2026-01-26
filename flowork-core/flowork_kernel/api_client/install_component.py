########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\api_client\install_component.py total lines 26 
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


def run(hub, zip_filepath: str):
    try:
        with open(zip_filepath, 'rb') as f:
            headers = hub.execute_sync('_get_local_auth_headers')
            files = {'file': (os.path.basename(zip_filepath), f, 'application/zip')}
            response = requests.post(f'{hub.local_base_url}/{component_type}/install', files=files, headers=headers)
        return hub.execute_sync('_handle_response', response)
    except FileNotFoundError:
        return (False, f'Local file not found: {zip_filepath}')
    except requests.exceptions.ConnectionError as e:
        return (False, f'Connection to API server failed: {e}')

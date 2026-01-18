########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\api_client\upload_model.py total lines 26 
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


def run(hub, model_path: str, description: str, tier: str):
    try:
        form_data = {'description': description, 'tier': tier, 'model_id': os.path.basename(model_path).replace('.gguf', '')}
        with open(model_path, 'rb') as f:
            files = {'file': (os.path.basename(model_path), f, 'application/octet-stream')}
            response = requests.post(f'{hub.local_base_url}/models/upload', data=form_data, files=files, headers=hub.execute_sync('_get_local_auth_headers'))
        return hub.execute_sync('_handle_response', response)
    except FileNotFoundError:
        return (False, f'Local model file not found: {model_path}')
    except requests.exceptions.ConnectionError as e:
        return (False, f'Connection to API server failed: {e}')

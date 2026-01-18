########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\api_client\get_dashboard_layout.py total lines 22 
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


def run(hub, tab_id: str):
    try:
        response = requests.get(f'{hub.local_base_url}/uistate/dashboards/{tab_id}', headers=hub.execute_sync('_get_local_auth_headers'), timeout=3)
        return hub.execute_sync('_handle_response', response)
    except requests.exceptions.RequestException as e:
        error_message = hub.loc.get('api_connection_failed', fallback='Connection to API server failed: {error}', error=e) if hub.loc else f'Connection to API server failed: {e}'
        return (False, error_message)

########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\api_client\get_user_profile_by_token.py total lines 24 
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


def run(hub, session_token: str):
    if not hub.kernel.current_user:
        return (False, 'User profile not found in Kernel state. Authentication failed.')
    license_manager = hub.kernel.get_service('license_manager_service')
    user_data = hub.kernel.current_user.copy()
    user_data['message'] = 'Profile check successful (internal cache).'
    user_data['tier'] = hub.kernel.license_tier
    user_data['license_expires_at'] = license_manager.license_data.get('expiry_date') if license_manager and license_manager.license_data else None
    return (True, user_data)

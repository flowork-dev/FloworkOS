########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\vitality_service\_inject_doctor_reference.py total lines 27 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import time
import threading
import traceback
import asyncio
import json
from flowork_kernel.services.base_service import BaseService
from flowork_kernel.singleton import Singleton


def run(hub):
    """Mendaftarkan diri ke setiap service sebagai dokter pribadi mereka"""
    count = 0
    services_to_check = getattr(hub.kernel, 'services', {})
    for (s_id, service) in services_to_check.items():
        if hasattr(service, 'doctor'):
            service.doctor = hub
            service.is_active_service = True
            hub.patient_charts[s_id] = {'last_beat': time.time(), 'status': 'healthy'}
            count += 1
    if count > 0:
        hub.logger.info(f'💉 Injected Doctor to {count} services.')

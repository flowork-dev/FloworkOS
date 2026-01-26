########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\vitality_service\run_logic.py total lines 25 
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
    """Loop Utama Dokter: Memantau detak jantung sistem"""
    hub.logger.info('👨\u200d⚕️ VitalityService ON DUTY. Monitoring pulse...')
    hub.execute_sync('_inject_doctor_reference')
    while hub.is_running:
        try:
            hub.execute_sync('_check_all_patients')
            time.sleep(hub.check_interval)
        except Exception as e:
            hub.logger.error(f'Doctor error during rounds: {e}')

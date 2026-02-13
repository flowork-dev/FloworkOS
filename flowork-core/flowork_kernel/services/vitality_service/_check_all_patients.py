########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\vitality_service\_check_all_patients.py total lines 26 
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
    """Memastikan semua organ masih bernapas"""
    for (s_id, chart) in hub.patient_charts.items():
        if time.time() - chart['last_beat'] > 30:
            if chart['status'] != 'distress':
                chart['status'] = 'distress'
                hub.logger.warning(f"⚠️ Service '{s_id}' is unresponsive (Flatline detected).")

                hub.execute_sync('_notify_event_bus', 'SERVICE_HEALTH_UPDATE', {'service_id': s_id, 'status': 'unresponsive'})

                hub.execute_sync('_perform_cpr', s_id)

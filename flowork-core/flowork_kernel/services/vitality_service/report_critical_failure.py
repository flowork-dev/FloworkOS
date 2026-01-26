########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\vitality_service\report_critical_failure.py total lines 20 
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


def run(hub, service_id, stack_trace):
    """Menerima panggilan darurat dari service yang sekarat"""
    hub.logger.critical(f'🚑 EMERGENCY CALL from {service_id}!')
    hub.execute_sync('_notify_event_bus', 'SERVICE_CRITICAL_FAILURE', {'service_id': service_id, 'error': str(stack_trace), 'action': 'CPR_INITIATED'})
    threading.Thread(target=hub._perform_cpr, args=(service_id,), daemon=True).start()

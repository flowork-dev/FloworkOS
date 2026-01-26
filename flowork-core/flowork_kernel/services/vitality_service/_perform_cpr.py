########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\vitality_service\_perform_cpr.py total lines 41 
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


def run(hub, service_id):
    """Logika Penyelamatan (Defibrillator)"""
    hub.logger.info(f'⚡ Performing CPR on {service_id}...')
    try:
        app_manager = hub.kernel.get_service('app_service')

        if app_manager and service_id.startswith('app_'):
            app_id = service_id.replace('app_', '')
            hub.logger.info(f"🚑 [Lazarus] Restarting App Daemon: {app_id}")
            app_manager.ensure_app_running(app_id)
            hub.logger.info(f'✅ CPR Successful for App {app_id}')
            return True

        services = getattr(hub.kernel, 'services', {})
        patient = services.get(service_id)
        if patient and hasattr(patient, 'start'):
            if asyncio.iscoroutinefunction(patient.start):
                pass
            else:
                patient.start()
            hub.logger.info(f'✅ CPR Successful for Service {service_id}')
        else:
            hub.logger.warning(f'❌ CPR Failed: No recovery path for {service_id}')

    except Exception as e:
        hub.logger.error(f'❌ CPR Error for {service_id}: {e}')

########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\metrics_service\start.py total lines 20 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import threading
import time
import psutil
import os
from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY


def run(hub):
    if hasattr(hub, 'stop_event'):
        hub.stop_event.clear()

    hub.update_thread = threading.Thread(target=hub._update_system_metrics, daemon=True)
    hub.update_thread.start()
    hub.execute_sync('logger', 'MetricsService: Background monitoring started.', 'SUCCESS')

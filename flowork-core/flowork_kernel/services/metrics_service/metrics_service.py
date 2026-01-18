########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\metrics_service\metrics_service.py total lines 69 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from flowork_kernel.services.base_service import BaseService
import importlib
import logging
import threading
import os
import psutil
from prometheus_client import Counter, Histogram, Gauge, REGISTRY

class MetricsService(BaseService):
    def __init__(self, kernel, service_id: str):
        self.cells = {}
        if not hasattr(self, 'logger'): self.logger = logging.getLogger('LazyHub')
        super().__init__(kernel, service_id)

        self.stop_event = threading.Event()
        self.update_thread = None

        self.process = psutil.Process(os.getpid())
        for coll in list(REGISTRY._collector_to_names.keys()):
            try: REGISTRY.unregister(coll)
            except: pass

        self.WORKFLOWS_TOTAL = Counter('flowork_workflows_processed_total', 'Total workflows', ['status'])
        self.WORKFLOW_DURATION = Histogram('flowork_workflow_duration_seconds', 'Workflow duration')
        self.CPU_USAGE = Gauge('flowork_cpu_usage_percent', 'CPU Usage')
        self.MEMORY_USAGE_MB = Gauge('flowork_memory_usage_mb', 'Memory Usage')

    def execute_sync(self, cell_name, *args, **kwargs):
        """
        Menjalankan logika modul (cell) secara synchronous.
        """
        m = self._load_cell(cell_name)
        return m.run(self, *args, **kwargs) if m else None

    async def execute_async(self, cell_name, *args, **kwargs):
        """
        Menjalankan logika modul (cell) secara asynchronous.
        """
        m = self._load_cell(cell_name)
        return await m.run(self, *args, **kwargs) if m else None

    def _load_cell(self, cell_name):
        """
        Dynamic loader untuk memuat file-file kecil (cells) di dalam folder service.
        """
        if cell_name == 'logger': return None

        if cell_name not in self.cells:
            try:
                module = importlib.import_module(f".{cell_name}", package=__package__)
                self.cells[cell_name] = module
            except Exception as e:
                self.logger.error(f"Failed to load {cell_name}: {e}")
                raise e
        return self.cells[cell_name]

    def start(self, *args, **kwargs): return self.execute_sync('start', *args, **kwargs)
    def stop(self, *args, **kwargs): return self.execute_sync('stop', *args, **kwargs)
    def _update_system_metrics(self, *args, **kwargs): return self.execute_sync('_update_system_metrics', *args, **kwargs)
    def serve_metrics(self, *args, **kwargs): return self.execute_sync('serve_metrics', *args, **kwargs)
    def get_metrics(self, *args, **kwargs):
        try: return self.execute_sync('get_metrics', *args, **kwargs)
        except: return {}

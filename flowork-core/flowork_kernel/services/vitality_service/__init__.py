########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\vitality_service\__init__.py total lines 61 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import importlib
import os
import logging
import asyncio
import time
import threading
import traceback
import asyncio
import json
from flowork_kernel.services.base_service import BaseService
from flowork_kernel.singleton import Singleton


class VitalityService(BaseService):
    def __init__(self, kernel, service_id):
        self.cells = {}
        if not hasattr(self, 'logger'):
            self.logger = logging.getLogger('LazyHub')
        super().__init__(kernel, service_id)
        self.patient_charts = {}
        self.check_interval = 10

    def execute_sync(self, cell_name, *args, **kwargs):
        module = self._load_cell(cell_name)
        return module.run(self, *args, **kwargs)

    async def execute_async(self, cell_name, *args, **kwargs):
        module = self._load_cell(cell_name)
        return await module.run(self, *args, **kwargs)

    def _load_cell(self, cell_name):
        if cell_name not in self.cells:
            try:
                module = importlib.import_module(f".{cell_name}", package=__package__)
                self.cells[cell_name] = module
                if hasattr(self, 'logger'):
                    self.logger.info(f"[LazyHub] ✅ Loaded: {cell_name}.py")
            except Exception as e:
                if hasattr(self, 'logger'):
                    self.logger.error(f"[LazyHub] ❌ Failed to load '{cell_name}': {e}")
                raise e
        return self.cells[cell_name]

    def run_logic(self, *args, **kwargs):
        return self.execute_sync('run_logic', *args, **kwargs)
    def _inject_doctor_reference(self, *args, **kwargs):
        return self.execute_sync('_inject_doctor_reference', *args, **kwargs)
    def report_critical_failure(self, *args, **kwargs):
        return self.execute_sync('report_critical_failure', *args, **kwargs)
    def _perform_cpr(self, *args, **kwargs):
        return self.execute_sync('_perform_cpr', *args, **kwargs)
    def _check_all_patients(self, *args, **kwargs):
        return self.execute_sync('_check_all_patients', *args, **kwargs)
    def _notify_event_bus(self, *args, **kwargs):
        return self.execute_sync('_notify_event_bus', *args, **kwargs)

########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\job_orchestrator_service\__init__.py total lines 110 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from flowork_kernel.services.base_service import BaseService

import importlib
import os
import logging
import asyncio
import sqlite3
import json
import time
import uuid
import threading
import traceback

class JobOrchestratorService(BaseService):
    PRIORITY_HIGH = 100
    PRIORITY_MEDIUM = 50
    PRIORITY_LOW = 10

    def __init__(self, kernel, service_id: str):
        self.cells = {}
        if not hasattr(self, 'logger'):
            self.logger = logging.getLogger('LazyHub')
        super().__init__(kernel, service_id)

        self.data_path = '/app/data'
        if hasattr(self.kernel, 'data_path'):
            self.data_path = self.kernel.data_path

        self.db_path = os.path.join(self.data_path, 'global_jobs.db')
        self.db_lock = threading.Lock()
        self.resource_status = {'GPU': 'IDLE', 'CPU': 'IDLE'}

        self._init_db()

        self.running = True
        self.worker_thread = threading.Thread(target=self._orchestrator_loop, daemon=True)
        self.worker_thread.start()

        print(f'[JobOrchestrator] ✅ Service Online. Database: {self.db_path}')

    def _load_cell(self, cell_name):
        if cell_name not in self.cells:
            try:
                module = importlib.import_module(f".{cell_name}", package=__package__)
                self.cells[cell_name] = module
                if hasattr(self, 'logger'):
                    self.logger.info(f"[LazyHub] ✅ Loaded Atomic Cell: {cell_name}.py")
            except Exception as e:
                error_msg = f"[LazyHub] ❌ Failed to load '{cell_name}': {e}"
                if hasattr(self, 'logger'):
                    self.logger.error(error_msg)
                print(error_msg)
                raise e
        return self.cells[cell_name]

    def execute_sync(self, cell_name, *args, **kwargs):
        """Menjalankan cell synchronous (blocking/thread safe)"""
        module = self._load_cell(cell_name)
        return module.run(self, *args, **kwargs)

    async def execute(self, cell_name, *args, **kwargs):
        """Menjalankan cell asynchronous (coroutine) - Standard Hub Signature"""
        module = self._load_cell(cell_name)
        return await module.run(self, *args, **kwargs)

    async def execute_async(self, cell_name, *args, **kwargs):
        return await self.execute(cell_name, *args, **kwargs)


    def _init_db(self, *args, **kwargs):
        return self.execute_sync('_init_db', *args, **kwargs)

    def submit_job(self, *args, **kwargs):
        return self.execute_sync('submit_job', *args, **kwargs)

    def get_job_status(self, *args, **kwargs):
        return self.execute_sync('get_job_status', *args, **kwargs)

    def cancel_job(self, *args, **kwargs):
        return self.execute_sync('cancel_job', *args, **kwargs)

    def get_queue_list(self, *args, **kwargs):
        return self.execute_sync('get_queue_list', *args, **kwargs)

    def _orchestrator_loop(self, *args, **kwargs):
        return self.execute_sync('_orchestrator_loop', *args, **kwargs)

    def _fetch_next_job(self, *args, **kwargs):
        return self.execute_sync('_fetch_next_job', *args, **kwargs)

    def _execute_job(self, *args, **kwargs):
        return self.execute_sync('_execute_job', *args, **kwargs)

    def _update_job_status(self, *args, **kwargs):
        return self.execute_sync('_update_job_status', *args, **kwargs)

    def _dispatch_to_training_service(self, *args, **kwargs):
        return self.execute_sync('_dispatch_to_training_service', *args, **kwargs)

    def _dispatch_to_ai_service(self, *args, **kwargs):
        return self.execute_sync('_dispatch_to_ai_service', *args, **kwargs)

    def _dispatch_to_workflow_service(self, *args, **kwargs):
        return self.execute_sync('_dispatch_to_workflow_service', *args, **kwargs)

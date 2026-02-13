########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\workflow_executor_service\__init__.py total lines 103 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import importlib
import os
import logging
import asyncio
import logging
import uuid
import time
import json
import sqlite3
import multiprocessing
import asyncio
import random
import threading
from datetime import datetime
from typing import Dict, Any, List, Optional
from flowork_kernel.services.base_service import BaseService
from flowork_kernel.singleton import Singleton
from flowork_kernel.services.database_service.database_service import DatabaseService
from flowork_kernel.outcome import OutcomeMeter
from flowork_kernel.analyst import Analyst, AnalystReport


class WorkflowExecutorService(BaseService):
    def __init__(self, kernel, service_id):
        self.cells = {}
        if not hasattr(self, 'logger'):
            self.logger = logging.getLogger('LazyHub')
        super().__init__(kernel, service_id)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.event_bus = None
        self.execution_user_cache: Dict[str, str] = {}
        self.execution_loop_cache: Dict[str, Dict[str, Any]] = {}
        self._completion_lock = asyncio.Lock()
        self.app_manager = None
        self._watchdog_thread = None
        self.gateway_connector = None
        try:
            self.db_service = Singleton.get_instance(DatabaseService)
            if not self.db_service:
                self.logger.error('CRITICAL: Missing DB Service from Singleton.')
        except Exception as e:
            self.logger.error(f'CRITICAL: Failed to get Singleton instances: {e}')
            self.db_service = None

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

    def start_listeners(self, *args, **kwargs):
        return self.execute_sync('start_listeners', *args, **kwargs)
    def _watchdog_loop(self, *args, **kwargs):
        return self.execute_sync('_watchdog_loop', *args, **kwargs)
    def _queue_downstream_nodes_sync(self, *args, **kwargs):
        return self.execute_sync('_queue_downstream_nodes_sync', *args, **kwargs)
    def get_user_for_execution(self, *args, **kwargs):
        return self.execute_sync('get_user_for_execution', *args, **kwargs)
    def set_execution_loop_config(self, *args, **kwargs):
        return self.execute_sync('set_execution_loop_config', *args, **kwargs)
    def start_workflow_execution(self, *args, **kwargs):
        return self.execute_sync('start_workflow_execution', *args, **kwargs)
    async def _on_job_completed(self, *args, **kwargs):
        return await self.execute_async('_on_job_completed', *args, **kwargs)
    def _get_node_id_by_job(self, *args, **kwargs):
        return self.execute_sync('_get_node_id_by_job', *args, **kwargs)
    async def _queue_downstream_nodes(self, *args, **kwargs):
        return await self.execute_async('_queue_downstream_nodes', *args, **kwargs)
    async def _check_workflow_completion(self, *args, **kwargs):
        return await self.execute_async('_check_workflow_completion', *args, **kwargs)
    async def _handle_global_loop(self, *args, **kwargs):
        return await self.execute_async('_handle_global_loop', *args, **kwargs)
    def _generate_r5_report(self, *args, **kwargs):
        return self.execute_sync('_generate_r5_report', *args, **kwargs)
    def _publish_node_status(self, *args, **kwargs):
        return self.execute_sync('_publish_node_status', *args, **kwargs)
    def _publish_workflow_status(self, *args, **kwargs):
        return self.execute_sync('_publish_workflow_status', *args, **kwargs)
    def _publish_log(self, *args, **kwargs):
        return self.execute_sync('_publish_log', *args, **kwargs)
    async def execute_standalone_node(self, *args, **kwargs):
        return await self.execute_async('execute_standalone_node', *args, **kwargs)

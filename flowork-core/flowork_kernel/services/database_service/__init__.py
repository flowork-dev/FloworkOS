########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\database_service\__init__.py total lines 87 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import importlib
import os
import logging
import asyncio
import sqlite3
import json
import uuid
import inspect
from flowork_kernel.services.base_service import BaseService
from flowork_kernel.singleton import Singleton

DB_SCHEMA_VERSION = 9 # Synchronized with create_tables.py (v9)

class DatabaseService(BaseService):
    def __init__(self, kernel, service_id, db_name='flowork_core.db'):
        self.cells = {}
        if not hasattr(self, 'logger'):
            self.logger = logging.getLogger('LazyHub')
        super().__init__(kernel, service_id)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.data_dir = self.kernel.data_path
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        self.db_path = os.path.join(self.data_dir, db_name)
        self.logger.info(f'DatabaseService initialized. DB Path: {self.db_path}')

        self._discover_cells()
        self.create_tables()

    def _discover_cells(self):
        """Dynamic Component Discovery (DCD)"""
        package_path = os.path.dirname(__file__)
        if not os.path.exists(package_path): return
        for file in os.listdir(package_path):
            if file.endswith(".py") and not file.startswith("__"):
                cell_name = file[:-3]
                if not hasattr(self, cell_name):
                    setattr(self, cell_name, self._make_executor(cell_name))

    def _make_executor(self, cell_name):
        def wrapper(*args, **kwargs):
            return self.execute_sync(cell_name, *args, **kwargs)
        return wrapper

    def execute_sync(self, cell_name, *args, **kwargs):
        module = self._load_cell(cell_name)
        if inspect.iscoroutinefunction(module.run):
            self.logger.warning(f"⚠️ Cell '{cell_name}' is async but called via execute_sync!")
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return asyncio.run_coroutine_threadsafe(module.run(self, *args, **kwargs), loop).result()
            else:
                return loop.run_until_complete(module.run(self, *args, **kwargs))
        return module.run(self, *args, **kwargs)

    async def execute_async(self, cell_name, *args, **kwargs):
        module = self._load_cell(cell_name)
        if inspect.iscoroutinefunction(module.run):
            return await module.run(self, *args, **kwargs)
        return module.run(self, *args, **kwargs)

    def _load_cell(self, cell_name):
        if cell_name not in self.cells:
            try:
                module = importlib.import_module(f".{cell_name}", package=__package__)
                self.cells[cell_name] = module
                self.logger.info(f"[LazyHub] ✅ Loaded: {cell_name}.py")
            except Exception as e:
                self.logger.error(f"[LazyHub] ❌ Failed to load '{cell_name}': {e}")
                raise e
        return self.cells[cell_name]

    def create_connection(self, *args, **kwargs): return self.execute_sync('create_connection', *args, **kwargs)
    def get_connection(self, *args, **kwargs): return self.execute_sync('get_connection', *args, **kwargs)
    def transaction(self, *args, **kwargs): return self.execute_sync('transaction', *args, **kwargs)
    def execute_app_query(self, *args, **kwargs): return self.execute_sync('execute_app_query', *args, **kwargs)
    def _perform_db_operation(self, *args, **kwargs): return self.execute_sync('_perform_db_operation', *args, **kwargs)
    def create_tables(self, *args, **kwargs): return self.execute_sync('create_tables', *args, **kwargs)
    def get_all_storage(self, *args, **kwargs): return self.execute_sync('get_all_storage', *args, **kwargs)
    def start(self, *args, **kwargs): return self.execute_sync('start', *args, **kwargs)
    def stop(self, *args, **kwargs): return self.execute_sync('stop', *args, **kwargs)

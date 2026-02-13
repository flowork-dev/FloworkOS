########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\cloud_sync_service\__init__.py total lines 64 
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
import os
import shutil
import base64
import requests
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet
import zipfile
import tempfile


class CloudSyncService(BaseService):
    TIER_REQUIREMENT = 'creator'

    def __init__(self, kernel, service_id: str):
        self.cells = {}
        if not hasattr(self, 'logger'):
            self.logger = logging.getLogger('LazyHub')
        super().__init__(kernel, service_id)
        self.users_data_path = os.path.join(self.kernel.data_path, 'users')

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

    def _generate_key_from_password(self, *args, **kwargs):
        return self.execute_sync('_generate_key_from_password', *args, **kwargs)
    def _get_user_data_path(self, *args, **kwargs):
        return self.execute_sync('_get_user_data_path', *args, **kwargs)
    def _create_zip_from_user_data(self, *args, **kwargs):
        return self.execute_sync('_create_zip_from_user_data', *args, **kwargs)
    def encrypt_and_upload_backup(self, *args, **kwargs):
        return self.execute_sync('encrypt_and_upload_backup', *args, **kwargs)
    def download_and_decrypt_backup(self, *args, **kwargs):
        return self.execute_sync('download_and_decrypt_backup', *args, **kwargs)

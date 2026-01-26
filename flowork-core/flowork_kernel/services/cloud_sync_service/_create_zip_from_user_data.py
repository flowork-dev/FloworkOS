########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\cloud_sync_service\_create_zip_from_user_data.py total lines 28 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import shutil
import base64
import requests
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet
import zipfile
import tempfile


def run(hub, user_id: str) -> str:
    user_folder = hub.execute_sync('_get_user_data_path', user_id)
    if not os.path.isdir(user_folder):
        raise FileNotFoundError(f'User data directory not found for user_id: {user_id}')
    temp_dir = os.path.join(hub.kernel.data_path, 'temp_sync')
    os.makedirs(temp_dir, exist_ok=True)
    output_zip_path = os.path.join(temp_dir, f'backup_{user_id}')
    hub.execute_sync('logger', f"Creating zip archive for user '{user_id}'...", 'INFO')
    shutil.make_archive(output_zip_path, 'zip', user_folder)
    hub.execute_sync('logger', f'Successfully created zip archive at: {output_zip_path}.zip', 'SUCCESS')
    return f'{output_zip_path}.zip'

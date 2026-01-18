########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\cloud_sync_service\encrypt_and_upload_backup.py total lines 49 
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


def run(hub, user_id: str, password: str):
    permission_manager = hub.kernel.get_service('permission_manager_service')
    if permission_manager:
        permission_manager.check_permission(hub.TIER_REQUIREMENT)
    if not password:
        return (False, 'Password is required for encryption.')
    try:
        zip_path = hub.execute_sync('_create_zip_from_user_data', user_id)
        salt = os.urandom(16)
        key = hub.execute_sync('_generate_key_from_password', password, salt)
        fernet = Fernet(key)
        hub.execute_sync('logger', f"Encrypting data for user '{user_id}'...", 'INFO')
        with open(zip_path, 'rb') as f:
            zip_data = f.read()
        encrypted_data = fernet.encrypt(zip_data)
        hub.execute_sync('logger', f'Encryption successful.', 'SUCCESS')
        os.remove(zip_path)
        files = {'backup_file': ('backup.zip.enc', encrypted_data, 'application/octet-stream')}
        payload = {'user_id': user_id, 'salt': base64.b64encode(salt).decode('utf-8')}
        hub.execute_sync('logger', f'Uploading encrypted backup to Gateway...', 'INFO')
        gateway_url = 'https://api.flowork.cloud'
        upload_endpoint = f'{gateway_url}/api/v1/engine/sync/upload-backup'
        headers = {'X-API-Key': os.getenv('GATEWAY_SECRET_TOKEN')}
        response = requests.post(upload_endpoint, files=files, data=payload, headers=headers)
        response.raise_for_status()
        hub.execute_sync('logger', f'Upload successful! Gateway responded: {response.json()}', 'SUCCESS')
        return (True, 'Backup successful!')
    except Exception as e:
        hub.execute_sync('logger', f'An error occurred during the backup process: {e}', 'CRITICAL')
        import traceback
        hub.execute_sync('logger', traceback.format_exc(), 'DEBUG')
        return (False, str(e))

########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\cloud_sync_service\download_and_decrypt_backup.py total lines 69 
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
        return (False, 'Password is required for decryption.')
    hub.execute_sync('logger', f"Starting restore process for user '{user_id}'...", 'INFO')
    try:
        gateway_url = 'https://api.flowork.cloud'
        download_endpoint = f'{gateway_url}/api/v1/engine/sync/download-backup'
        headers = {'X-API-Key': os.getenv('GATEWAY_SECRET_TOKEN')}
        params = {'user_id': user_id}
        hub.execute_sync('logger', f'Requesting encrypted backup from Gateway...', 'INFO')
        response = requests.get(download_endpoint, headers=headers, params=params)
        response.raise_for_status()
        encrypted_data = response.content
        salt_b64 = response.headers.get('X-Flowork-Salt')
        if not salt_b64:
            raise ValueError('Salt not found in response headers from Gateway.')
        salt = base64.b64decode(salt_b64)
        key = hub.execute_sync('_generate_key_from_password', password, salt)
        fernet = Fernet(key)
        hub.execute_sync('logger', f'Decrypting user data...', 'INFO')
        decrypted_zip_data = fernet.decrypt(encrypted_data)
        hub.execute_sync('logger', f'Decryption successful.', 'SUCCESS')
        temp_zip_path = os.path.join(tempfile.gettempdir(), f'restore_{user_id}.zip')
        with open(temp_zip_path, 'wb') as f:
            f.write(decrypted_zip_data)
        user_data_path = hub.execute_sync('_get_user_data_path', user_id)
        if os.path.isdir(user_data_path):
            hub.execute_sync('logger', f"Removing old user data at '{user_data_path}'...", 'WARN')
            shutil.rmtree(user_data_path)
        os.makedirs(user_data_path, exist_ok=True)
        hub.execute_sync('logger', f"Extracting backup to '{user_data_path}'...", 'INFO')
        with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
            zip_ref.extractall(user_data_path)
        os.remove(temp_zip_path)
        hub.execute_sync('logger', f"Restore process for user '{user_id}' completed successfully!", 'SUCCESS')
        hub.kernel.hot_reload_components()
        return (True, 'Restore completed successfully.')
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            hub.execute_sync('logger', f"No backup found on the server for user '{user_id}'.", 'WARN')
            return (False, 'No backup found on the server.')
        else:
            hub.execute_sync('logger', f'An HTTP error occurred during the restore process: {e.response.text}', 'CRITICAL')
            return (False, f'Server error: {e.response.text}')
    except Exception as e:
        hub.execute_sync('logger', f'An error occurred during the restore process: {e}', 'CRITICAL')
        import traceback
        hub.execute_sync('logger', traceback.format_exc(), 'DEBUG')
        return (False, str(e))

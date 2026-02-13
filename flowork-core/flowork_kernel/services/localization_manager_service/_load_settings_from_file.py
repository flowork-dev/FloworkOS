########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\localization_manager_service\_load_settings_from_file.py total lines 31 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import json
from collections import OrderedDict


def run(hub, user_id):
    settings_file_path = hub.execute_sync('_get_user_settings_path', user_id)
    try:
        current_settings = {}
        if os.path.exists(settings_file_path):
            with open(settings_file_path, 'r', encoding='utf-8') as f:
                current_settings = json.load(f)
        default_webhook_port = int(os.getenv('CORE_API_PORT', 8989))
        defaults = {'active_template': 'default', 'language': 'en', 'ai_gpu_layers': -1, 'ai_worker_timeout_seconds': 600, 'webhook_enabled': True, 'webhook_port': default_webhook_port, 'global_error_handler_enabled': False, 'global_error_workflow_preset': '', 'last_run_time': None, 'notifications_enabled': True, 'notifications_duration_seconds': 5, 'notifications_position': 'bottom_right'}
        settings_changed = False
        for (key, value) in defaults.items():
            if key not in current_settings:
                current_settings[key] = value
                settings_changed = True
        if settings_changed:
            hub.execute_sync('_save_settings', current_settings, user_id)
        return current_settings
    except Exception as e:
        hub.kernel.write_to_log(f"LocalizationManager: Failed to load settings for user '{user_id}': {e}", 'ERROR')
        return {}

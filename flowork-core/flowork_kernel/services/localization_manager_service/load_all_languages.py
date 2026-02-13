########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\localization_manager_service\load_all_languages.py total lines 25 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import json
from collections import OrderedDict


def run(hub):
    hub.kernel.write_to_log('LocalizationManager: Starting full language scan and merge...', 'INFO')
    hub.languages.clear()
    hub.execute_sync('load_base_languages')
    app_service = hub.kernel.get_service('app_service', is_system_call=True)
    component_managers = {'modules': app_service, 'plugins': app_service, 'widgets': app_service, 'triggers': app_service, 'tools': app_service, 'ai_providers': hub.kernel.get_service('ai_provider_manager_service', is_system_call=True)}
    for (manager_name, manager) in component_managers.items():
        if manager and hasattr(manager, f'loaded_{manager_name}'):
            items_to_scan = getattr(manager, f'loaded_{manager_name}', {})
            for (item_id, item_data) in items_to_scan.items():
                if isinstance(item_data, dict) and item_data.get('path'):
                    component_locales_path = os.path.join(item_data['path'], 'locales')
                    hub.execute_sync('_merge_from_directory', component_locales_path, source_name=item_id)
    hub.kernel.write_to_log('LocalizationManager: Language merge complete.', 'SUCCESS')
